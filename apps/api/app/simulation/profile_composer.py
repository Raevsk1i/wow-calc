from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.config import Settings
from app.domain.models import (
    Role,
    SimulationMode,
    SimulationRequest,
    SimulationSupport,
    Specialization,
)
from app.simulation.apl_mutator import (
    build_priority_apl,
    sanitize_skip_actions,
    validate_custom_apl,
)


@dataclass
class ComposedProfile:
    text: str
    warnings: list[str]
    assumptions: list[str] = field(default_factory=list)
    iterations: int = 100
    extra_args: list[str] = field(default_factory=list)


def _load_preset(settings: Settings, filename: str) -> str:
    path = Path(settings.simc_profiles_dir) / filename
    if not path.is_file():
        raise FileNotFoundError(f"Preset profile not found: {filename}")
    return path.read_text(encoding="utf-8")


def _strip_line_prefixes(profile: str, prefixes: tuple[str, ...]) -> str:
    kept: list[str] = []
    for line in profile.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(prefix) for prefix in prefixes):
            continue
        kept.append(line)
    return "\n".join(kept).rstrip() + "\n"


def _apply_stat_overrides(profile: str, request: SimulationRequest) -> tuple[str, list[str]]:
    warnings: list[str] = []
    stats = request.gear.customStats
    if not stats:
        return profile, warnings

    overrides: list[str] = []
    if stats.primaryStat is not None:
        overrides.append(f"# custom primaryStat={stats.primaryStat}")
        warnings.append("Custom primary stat applied as documentation override only when gear lines exist.")
    if stats.crit is not None:
        overrides.append(f"crit_rating={stats.crit}")
    if stats.haste is not None:
        overrides.append(f"haste_rating={stats.haste}")
    if stats.mastery is not None:
        overrides.append(f"mastery_rating={stats.mastery}")
    if stats.versatility is not None:
        overrides.append(f"versatility_rating={stats.versatility}")
    if not overrides:
        return profile, warnings
    return profile.rstrip() + "\n" + "\n".join(overrides) + "\n", warnings


def _resolve_iterations(request: SimulationRequest, settings: Settings) -> int:
    mode = request.fight.mode
    if request.fight.iterations is not None:
        cap = (
            settings.max_iterations_monte_carlo
            if mode.is_final()
            else settings.max_iterations_preview
        )
        return max(1, min(request.fight.iterations, cap))
    if mode.is_final():
        return min(settings.max_iterations_monte_carlo, settings.max_iterations_monte_carlo)
    if mode in {SimulationMode.accurate}:
        return settings.max_iterations_accurate
    return settings.max_iterations_preview


def _apply_raid_config(profile: str, request: SimulationRequest) -> tuple[str, list[str], list[str]]:
    warnings: list[str] = []
    assumptions: list[str] = []
    raid = request.raid
    lines: list[str] = ["", "# Raid buffs / debuffs (independent toggles)"]

    if raid.optimalRaid is True:
        lines.append("optimal_raid=1")
        assumptions.append("optimal_raid=1 enabled (full standard raid buff set).")
    elif raid.optimalRaid is False:
        lines.append("optimal_raid=0")
        assumptions.append("optimal_raid=0 — individual buff toggles follow.")

    # Document toggles for reproducibility even when SimC maps them via optimal_raid.
    toggle_map = {
        "arcaneIntellect": raid.arcaneIntellect,
        "battleShout": raid.battleShout,
        "markOfTheWild": raid.markOfTheWild,
        "skyfury": raid.skyfury,
        "chaosBrand": raid.chaosBrand,
        "mysticTouch": raid.mysticTouch,
    }
    for key, enabled in toggle_map.items():
        lines.append(f"# raid.{key}={'on' if enabled else 'off'}")
        assumptions.append(f"{key}={'on' if enabled else 'off'}")

    if raid.bloodlust.enabled:
        # SimC: bloodlust / potion timing via override; use fixed at-time comment + enable.
        at_s = max(0, raid.bloodlust.atMs) / 1000.0
        lines.append("bloodlust=1")
        lines.append(f"# bloodlust_at_s={at_s:.3f}")
        assumptions.append(f"Bloodlust enabled (requested at {at_s:.1f}s).")
    else:
        lines.append("bloodlust=0")
        assumptions.append("Bloodlust disabled.")

    if raid.optimalRaid is None and all(toggle_map.values()) and raid.bloodlust.enabled:
        # Default UX: full buffs → optimal_raid for SimC correctness.
        lines.append("optimal_raid=1")
        assumptions.append("Defaulted optimal_raid=1 because all standard raid toggles are on.")
    elif raid.optimalRaid is None and not all(toggle_map.values()):
        lines.append("optimal_raid=0")
        warnings.append(
            "Partial raid buff selection: optimal_raid=0. "
            "SimC may not perfectly mirror every individual Midnight buff toggle."
        )

    return profile.rstrip() + "\n" + "\n".join(lines) + "\n", warnings, assumptions


def _apply_role_options(
    profile: str,
    request: SimulationRequest,
    spec: Specialization | None,
) -> tuple[str, list[str], list[str]]:
    warnings: list[str] = []
    assumptions: list[str] = []
    lines: list[str] = []

    role = spec.role if spec else None
    if role == Role.tank:
        lines.append("position=front")
        assumptions.append("Tank position=front for offensive_tank simulation.")
        model = request.incomingDamageModel
        if model is None:
            from app.domain.models import IncomingDamageModel

            model = IncomingDamageModel()
        if model.enabled:
            lines.append(
                "# incomingDamageModel "
                f"aps={model.attacksPerSecond} "
                f"physical={model.physicalFraction} magic={model.magicFraction}"
            )
            # Approximate reactive uptime using SimC override where available.
            lines.append(f"override.enemy_attack_speed={model.attacksPerSecond}")
            warnings.append(
                "Tank incomingDamageModel is an approximation for reactive procs; "
                "not a full mitigation sim."
            )
            assumptions.append(
                f"Incoming attacks ≈ {model.attacksPerSecond}/s "
                f"({model.physicalFraction:.0%} physical / {model.magicFraction:.0%} magic)."
            )
        else:
            warnings.append("Tank incomingDamageModel disabled — reactive procs may be undercounted.")

    if role == Role.healer:
        profile_cfg = request.healerDamageProfile
        if profile_cfg is None:
            from app.domain.models import HealerDamageProfile

            profile_cfg = HealerDamageProfile()
        assumptions.append(
            f"Healer damageActivity={profile_cfg.damageActivity:.2f}, "
            f"healingActivity={profile_cfg.healingActivity:.2f}."
        )
        if profile_cfg.damageActivity < 1.0:
            warnings.append(
                "Healer damageActivity < 1.0: personal DPS will be scaled after the sim "
                "(healing actions are not fully modeled)."
            )
        else:
            assumptions.append("Healer damage-only mode (100% offensive activity).")

    if role == Role.dps:
        lines.append("position=back")
        assumptions.append("DPS position=back.")

    if role == Role.support:
        assumptions.append("Augmentation/support: personal DPS from SimC; contribution is separate.")

    if request.fight.clusterRadiusYards is not None:
        lines.append(f"# encounter.clusterRadiusYards={request.fight.clusterRadiusYards}")
        assumptions.append(f"Target cluster radius {request.fight.clusterRadiusYards} yd (documented).")

    if not lines:
        return profile, warnings, assumptions
    return profile.rstrip() + "\n" + "\n".join(lines) + "\n", warnings, assumptions


def compose_profile(
    request: SimulationRequest,
    *,
    settings: Settings,
    preset_filename: str,
    support: SimulationSupport,
    default_hero_talent: str | None = None,
    spec: Specialization | None = None,
) -> ComposedProfile:
    warnings: list[str] = []
    assumptions: list[str] = []

    if support == SimulationSupport.unsupported:
        raise ValueError("Specialization is unsupported for simulation")

    if request.gear.rawSimcProfile:
        profile = _sanitize_imported_profile(request.gear.rawSimcProfile)
        warnings.append("Using sanitized imported SimulationCraft profile text.")
    else:
        profile = _load_preset(settings, preset_filename)
        if request.talents.exportString:
            profile = _strip_line_prefixes(profile, ("talents=",))
            profile += f"talents={request.talents.exportString.strip()}\n"
        elif not request.talents.useProfileTalents:
            profile = _strip_line_prefixes(profile, ("talents=",))
            hero = request.talents.heroTalent or default_hero_talent
            if hero:
                profile += f"hero_talents={hero}\n"
                warnings.append(
                    f"Profile talent hash unused; applied hero_talents={hero}. "
                    "Import a valid talent string for accurate results."
                )
        elif default_hero_talent and "talents=" in profile:
            pass

        if request.gear.preset == "custom":
            profile, stat_warnings = _apply_stat_overrides(profile, request)
            warnings.extend(stat_warnings)
        elif request.gear.preset in {"mid", "entry"}:
            tier = "MID2" if "MID2" in preset_filename else "MID1"
            warnings.append(f"{request.gear.preset} gear aliases {tier} High for this snapshot.")

    profile += f"\ndesired_targets={request.fight.targets}\n"
    profile += f"max_time={request.fight.duration}\n"
    profile += f"fight_style={request.fight.fightStyle.value}\n"
    profile += f"gcd_lag={request.fight.latencyMs / 1000.0:.3f}\n"
    assumptions.append(
        f"Encounter: {request.fight.fightStyle.value}, {request.fight.targets} target(s), "
        f"{request.fight.duration}s."
    )

    profile, raid_warnings, raid_assumptions = _apply_raid_config(profile, request)
    warnings.extend(raid_warnings)
    assumptions.extend(raid_assumptions)

    profile, role_warnings, role_assumptions = _apply_role_options(profile, request, spec)
    warnings.extend(role_warnings)
    assumptions.extend(role_assumptions)

    if request.rotation.mode.value == "custom":
        if request.rotation.customApl:
            for line in validate_custom_apl(request.rotation.customApl):
                profile += line + "\n"
            warnings.append("Custom APL applied (allowlisted actions only).")
        elif request.rotation.priority:
            for line in build_priority_apl(request.rotation.priority):
                profile += line + "\n"
            warnings.append("Custom priority APL generated from allowlisted actions.")

        skip = sanitize_skip_actions(request.rotation.disabledActions)
        if skip:
            profile += f"skip_actions={skip}\n"
    else:
        skip = sanitize_skip_actions(request.rotation.disabledActions)
        if skip:
            profile += f"skip_actions={skip}\n"
            warnings.append(f"Disabled actions via skip_actions={skip}")

    iterations = _resolve_iterations(request, settings)
    mode_label = "monte_carlo" if request.fight.mode.is_final() else "preview"
    assumptions.append(f"Simulation mode={mode_label}, iterations={iterations}.")

    extra_args = [
        f"iterations={iterations}",
        f"threads={settings.simc_threads}",
        "target_error=0",
    ]
    if request.seed is not None:
        extra_args.append(f"seed={int(request.seed)}")

    if support == SimulationSupport.experimental:
        warnings.append("Specialization marked Experimental — interpret results cautiously.")
    if support == SimulationSupport.partial:
        warnings.append("Specialization marked Partial — coverage incomplete.")

    if spec and spec.role == Role.support:
        party = request.party
        if party is None or not party.enabled or not party.members:
            warnings.append("Augmentation: Personal DPS only (party contribution model disabled).")
            assumptions.append("Augmentation result labeled Personal DPS only.")
        else:
            assumptions.append(
                f"Augmentation party model enabled with {len(party.members)} ally baseline(s)."
            )

    return ComposedProfile(
        text=profile,
        warnings=warnings,
        assumptions=assumptions,
        iterations=iterations,
        extra_args=extra_args,
    )


def profile_without_talents_hash(profile_text: str, hero_talent: str | None) -> str:
    text = _strip_line_prefixes(profile_text, ("talents=", "hero_talents="))
    if hero_talent:
        text += f"hero_talents={hero_talent}\n"
    return text


def compute_augmentation_contribution(
    personal_dps: float,
    request: SimulationRequest,
    spec: Specialization,
) -> tuple[float | None, float | None, list[str], list[str]]:
    """Estimate external contribution from curated buffFactors × ally baselines."""
    warnings: list[str] = []
    assumptions: list[str] = []
    party = request.party
    if party is None or not party.enabled or not party.members:
        return None, None, warnings, assumptions

    model = spec.augmentationModel
    if model is None or not model.buffFactors:
        warnings.append("Augmentation contribution requested but no curated buffFactors in catalog.")
        return None, None, warnings, assumptions

    factor = sum(model.buffFactors.values())
    external = sum(m.baselineDps for m in party.members) * factor
    effective = personal_dps + external
    assumptions.append(
        f"externalContributionDps ≈ Σ(allyBaseline) × {factor:.4f} "
        f"from curated factors {model.buffFactors}."
    )
    warnings.append(
        "Augmentation externalContributionDps is a curated estimate, not a full multi-actor SimC raid."
    )
    if model.notes:
        assumptions.append(model.notes)
    return external, effective, warnings, assumptions


def _sanitize_imported_profile(raw: str) -> str:
    if len(raw) > 200_000:
        raise ValueError("Imported profile too large")
    kept: list[str] = []
    for raw_line in raw.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            kept.append(raw_line)
            continue
        if "=" not in line:
            continue
        key = line.split("=", 1)[0].strip().lower()
        base = key.split(".", 1)[0]
        forbidden = {
            "threads",
            "html",
            "xml",
            "json",
            "json2",
            "output",
            "save",
            "armory",
            "guild",
            "wowhead",
            "local_json",
            "proxy",
            "input",
        }
        if base in forbidden or key in forbidden:
            continue
        kept.append(raw_line)
    return "\n".join(kept).rstrip() + "\n"
