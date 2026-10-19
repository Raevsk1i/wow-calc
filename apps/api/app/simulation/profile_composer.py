from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.config import Settings
from app.domain.models import ReadinessStatus, RotationMode, SimulationMode, SimulationRequest
from app.simulation.apl_mutator import (
    build_priority_apl,
    sanitize_skip_actions,
    validate_custom_apl,
)


@dataclass
class ComposedProfile:
    text: str
    warnings: list[str]
    iterations: int
    extra_args: list[str]


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

    # SimC accepts gear_strength / crit_rating style overrides after the actor block.
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


def _apply_raid_options(profile: str, request: SimulationRequest) -> tuple[str, list[str]]:
    """Emit discrete raid buff/debuff toggles — never a single raidDamageMultiplier."""
    warnings: list[str] = []
    raid = request.fight.raid
    lines: list[str] = []
    # SimC accepts override.bloodlust / similar; keep portable comments + safe options.
    lines.append(f"# raid.arcane_intellect={int(raid.arcaneIntellect)}")
    lines.append(f"# raid.battle_shout={int(raid.battleShout)}")
    lines.append(f"# raid.mark_of_the_wild={int(raid.markOfTheWild)}")
    lines.append(f"# raid.skyfury={int(raid.skyfury)}")
    lines.append(f"# raid.chaos_brand={int(raid.chaosBrand)}")
    lines.append(f"# raid.mystic_touch={int(raid.mysticTouch)}")
    if raid.bloodlust:
        lines.append("override.bloodlust=1")
        if raid.bloodlustAtMs > 0:
            lines.append(f"# bloodlust_at_ms={raid.bloodlustAtMs}")
    else:
        lines.append("override.bloodlust=0")
        warnings.append("Bloodlust disabled for this Accurate run")
    if request.fight.incomingDamage:
        lines.append("# encounter.incoming_damage=1")
    if request.fight.clusterRadiusYards:
        lines.append(f"# encounter.cluster_radius_yards={request.fight.clusterRadiusYards}")
    return profile.rstrip() + "\n" + "\n".join(lines) + "\n", warnings


def compose_profile(
    request: SimulationRequest,
    *,
    settings: Settings,
    preset_filename: str,
    support: ReadinessStatus,
    default_hero_talent: str | None = None,
) -> ComposedProfile:
    warnings: list[str] = []

    if support == ReadinessStatus.unsupported:
        raise ValueError("Specialization is unsupported for Accurate simulation")

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

    profile += f"\ndesired_targets={request.fight.targets}\n"
    profile += f"max_time={request.fight.duration}\n"
    profile += f"fight_style={request.fight.fightStyle.value}\n"
    profile += f"gcd_lag={request.fight.latencyMs / 1000.0:.3f}\n"
    profile, raid_warnings = _apply_raid_options(profile, request)
    warnings.extend(raid_warnings)

    mode = request.rotation.mode
    use_custom = mode in {
        RotationMode.custom,
        RotationMode.burst_focus,
        RotationMode.sustained,
        RotationMode.aoe_optimization,
    }
    if use_custom and mode != RotationMode.custom:
        warnings.append(f"Rotation profile={mode.value} — using priority/skip mutations on default APL")

    if mode == RotationMode.custom:
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

    if request.fight.mode == SimulationMode.accurate:
        iterations = request.fight.iterations or settings.max_iterations_accurate
    else:
        # Legacy "quick" Accurate path (low iterations)
        iterations = request.fight.iterations or settings.max_iterations_quick
    iterations = max(1, min(iterations, settings.max_iterations_accurate))

    extra_args = [
        f"iterations={iterations}",
        f"threads={settings.simc_threads}",
        "target_error=0",
    ]
    if request.seed is not None:
        extra_args.append(f"seed={int(request.seed)}")

    if support in {ReadinessStatus.partial, ReadinessStatus.implemented}:
        warnings.append(f"Specialization readiness={support.value}")

    return ComposedProfile(
        text=profile,
        warnings=warnings,
        iterations=iterations,
        extra_args=extra_args,
    )


def profile_without_talents_hash(profile_text: str, hero_talent: str | None) -> str:
    text = _strip_line_prefixes(profile_text, ("talents=", "hero_talents="))
    if hero_talent:
        text += f"hero_talents={hero_talent}\n"
    return text


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
