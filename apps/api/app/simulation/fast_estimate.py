from __future__ import annotations

from app.config import Settings
from app.data.catalog import get_estimate_baselines, get_ruleset
from app.domain.models import (
    AbilityBreakdownRow,
    SimulationMode,
    SimulationRequest,
    SimulationResult,
    Specialization,
)
from app.simulation.engine import ISimulationEngine, ValidationResult


def _piecewise_dr(raw_pct: float, thresholds: list[dict]) -> float:
    """Apply rating diminishing returns to a raw percentage (0-1+)."""
    remaining = max(0.0, raw_pct)
    effective = 0.0
    prev = 0.0
    for band in thresholds:
        up_to = band.get("upTo")
        efficiency = float(band["efficiency"])
        if up_to is None:
            effective += remaining * efficiency
            break
        width = float(up_to) - prev
        take = min(remaining, width)
        effective += take * efficiency
        remaining -= take
        prev = float(up_to)
        if remaining <= 1e-12:
            break
    return effective


def rating_to_expected_multipliers(
    *,
    crit_rating: int | None,
    haste_rating: int | None,
    mastery_rating: int | None,
    vers_rating: int | None,
    ruleset: dict,
) -> dict[str, float]:
    cr = ruleset.get("combatRating") or {}
    thresholds = cr.get("diminishingReturns") or []
    crit_per = float(cr.get("critPerPercent") or 46)
    haste_per = float(cr.get("hastePerPercent") or 44)
    mastery_per = float(cr.get("masteryPerPoint") or 46)
    vers_per = float(cr.get("versatilityPerPercent") or 54)

    # Baseline MID profile assumed ~25% secondary packing before custom overrides.
    base_crit = 0.22
    base_haste = 0.20
    base_mastery_points = 0.25
    base_vers = 0.08

    if crit_rating is not None:
        base_crit = _piecewise_dr((crit_rating / crit_per) / 100.0, thresholds)
    if haste_rating is not None:
        base_haste = _piecewise_dr((haste_rating / haste_per) / 100.0, thresholds)
    if mastery_rating is not None:
        base_mastery_points = _piecewise_dr((mastery_rating / mastery_per) / 100.0, thresholds)
    if vers_rating is not None:
        base_vers = _piecewise_dr((vers_rating / vers_per) / 100.0, thresholds)

    # Expected damage multipliers (approximation, not full class mastery conversion).
    crit_mult = 1.0 + base_crit * (2.0 - 1.0)  # expected crit with Mcrit≈2
    haste_mult = 1.0 + base_haste * 0.55  # partial throughput mapping
    mastery_mult = 1.0 + base_mastery_points * 0.45
    vers_mult = 1.0 + base_vers
    return {
        "crit": crit_mult,
        "haste": haste_mult,
        "mastery": mastery_mult,
        "versatility": vers_mult,
        "combined": crit_mult * haste_mult * mastery_mult * vers_mult,
    }


def _aoe_factor(targets: int, aoe_class: str) -> float:
    if targets <= 1:
        return 1.0
    if aoe_class == "aoe":
        # Soft cap around 5 with diminishing beyond.
        if targets <= 5:
            return 1.0 + 0.55 * (targets - 1)
        return 1.0 + 0.55 * 4 + 0.15 * (targets - 5)
    if aoe_class == "cleave":
        return 1.0 + 0.35 * min(targets - 1, 2) + 0.08 * max(0, targets - 3)
    # single_target: small splash only
    return 1.0 + 0.02 * min(targets - 1, 3)


def _raid_multiplier(request: SimulationRequest, primary: str) -> tuple[float, list[str]]:
    raid = request.fight.raid
    assumptions: list[str] = []
    mult = 1.0
    if primary == "intellect" and raid.arcaneIntellect:
        mult *= 1.03
        assumptions.append("Arcane Intellect +3% Intellect")
    if primary in {"strength", "agility"} and raid.battleShout:
        mult *= 1.05
        assumptions.append("Battle Shout +5% Attack Power")
    if raid.markOfTheWild:
        mult *= 1.015  # ~half of vers flat mapped into damage EV
        assumptions.append("Mark of the Wild (partial vers EV)")
    if raid.skyfury:
        mult *= 1.01
        assumptions.append("Skyfury (partial mastery EV)")
    if raid.bloodlust:
        # 40s of +30% haste on a fight ≈ duration-weighted
        duration = max(30, request.fight.duration)
        uptime = min(40.0, duration) / duration
        mult *= 1.0 + 0.30 * 0.55 * uptime
        assumptions.append(f"Bloodlust uptime≈{uptime:.2f}")
    if raid.chaosBrand:
        mult *= 1.015
        assumptions.append("Chaos Brand partial magic amp")
    if raid.mysticTouch:
        mult *= 1.02
        assumptions.append("Mystic Touch partial physical amp")
    return mult, assumptions


class FastEstimateEngine(ISimulationEngine):
    """Deterministic expected-value DPS estimate. Always isApproximation=true."""

    name = "fast_estimate"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def validate_request(
        self, request: SimulationRequest, spec: Specialization
    ) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []
        if not spec.canFastEstimate:
            errors.append(f"{spec.key} does not support Fast Estimate")
        if request.fight.targets < 1 or request.fight.targets > self.settings.max_targets:
            errors.append("Invalid target count")
        if spec.readiness and spec.readiness.value == "unsupported":
            warnings.append("Spec readiness is unsupported — estimate uses generic baseline shares")
        if spec.role.value == "HEALER":
            warnings.append("Healer estimate assumes configured damageActivityShare")
        if spec.allyModelRequired and not request.fight.allies.enabled:
            warnings.append("Augmentation ally model disabled — Personal DPS only")
        return ValidationResult(ok=not errors, errors=errors, warnings=warnings)

    def run(self, request: SimulationRequest, spec: Specialization) -> SimulationResult:
        validation = self.validate_request(request, spec)
        if not validation.ok:
            raise ValueError("; ".join(validation.errors))

        ruleset = get_ruleset()
        baselines = get_estimate_baselines().get("baselines") or {}
        base = baselines.get(spec.key) or {
            "baselineDps": 40000 if spec.role.value == "DPS" else 20000,
            "primary": spec.primaryStat,
            "shares": {"filler": 0.6, "spender": 0.4},
        }

        stats = request.gear.customStats
        mults = rating_to_expected_multipliers(
            crit_rating=stats.crit if stats else None,
            haste_rating=stats.haste if stats else None,
            mastery_rating=stats.mastery if stats else None,
            vers_rating=stats.versatility if stats else None,
            ruleset=ruleset,
        )
        raid_mult, raid_assumptions = _raid_multiplier(request, str(base.get("primary") or spec.primaryStat))

        ability_lookup = {a.simcAction: a for a in spec.abilities}
        shares: dict[str, float] = dict(base.get("shares") or {})
        disabled = set(request.rotation.disabledActions or [])
        # Redistribute disabled ability shares to remaining.
        removed = 0.0
        for act in list(shares):
            if act in disabled:
                removed += shares.pop(act)
        if shares and removed:
            scale = 1.0 + removed / sum(shares.values())
            shares = {k: v * scale * 0.92 for k, v in shares.items()}  # 8% efficiency loss when rebuilding
        elif not shares:
            shares = {"filler": 1.0}

        # Target scaling per ability aoe class
        scaled_shares: dict[str, float] = {}
        for name, share in shares.items():
            aoe = ability_lookup[name].aoeClass if name in ability_lookup else (
                "aoe" if name in {"aoe", "pets"} else "single_target"
            )
            scaled_shares[name] = share * _aoe_factor(request.fight.targets, aoe)

        share_sum = sum(scaled_shares.values()) or 1.0
        normalized = {k: v / share_sum for k, v in scaled_shares.items()}

        baseline_dps = float(base["baselineDps"])
        # Normalize baseline to ~1 target; apply EV multipliers.
        dps = baseline_dps * mults["combined"] / 1.35 * raid_mult
        # Re-anchor so share-weighted aoe expands total
        dps *= share_sum

        activity = request.fight.damageActivityShare
        if activity is None:
            activity = spec.damageActivityShareDefault
        activity = max(0.05, min(1.0, float(activity)))
        if spec.role.value == "HEALER":
            dps *= activity

        # Priority / rotation mode soft knobs
        if request.rotation.mode.value == "burst_focus":
            dps *= 1.03
        elif request.rotation.mode.value == "aoe_optimization" and request.fight.targets >= 3:
            dps *= 1.04
        elif request.rotation.mode.value == "sustained":
            dps *= 0.99

        personal = dps
        ally_attr = 0.0
        effective = personal
        warnings = list(validation.warnings)
        assumptions = [
            "Fast Estimate is a deterministic approximation — not Monte Carlo.",
            f"Baseline revision={get_estimate_baselines().get('revision')}",
            f"Stat EV multipliers combined={mults['combined']:.3f}",
            *raid_assumptions,
        ]

        if spec.allyModelRequired:
            if request.fight.allies.enabled:
                factor = float(base.get("allyBuffFactor") or 0.12)
                ally_attr = (
                    request.fight.allies.allyCount
                    * request.fight.allies.allyMeanDps
                    * factor
                    * request.fight.allies.buffUptime
                )
                effective = personal + ally_attr
                assumptions.append(
                    f"Aug ally attribution: {request.fight.allies.allyCount} allies × "
                    f"{request.fight.allies.allyMeanDps:.0f} × {factor} × uptime"
                )
            else:
                warnings.append("Augmentation: Personal DPS only — enable ally model for Effective Contribution")

        duration = float(request.fight.duration)
        breakdown: list[AbilityBreakdownRow] = []
        for name, share in sorted(normalized.items(), key=lambda kv: -kv[1]):
            ability_dps = personal * share
            breakdown.append(
                AbilityBreakdownRow(
                    name=name,
                    spellId=None,
                    damage=ability_dps * duration,
                    pctTotal=share * 100.0,
                    casts=max(1.0, duration / 3.0 * share * 10),
                    avgHit=ability_dps * 1.5,
                    dps=ability_dps,
                )
            )

        ruleset_meta = get_ruleset()
        return SimulationResult(
            meanDps=effective if spec.allyModelRequired and request.fight.allies.enabled else personal,
            personalDps=personal,
            effectiveDps=effective if spec.allyModelRequired else None,
            allyAttributedDps=ally_attr if ally_attr else None,
            minDps=personal * 0.97,
            maxDps=personal * 1.03,
            medianDps=personal,
            stdDev=None,
            meanStdDev=None,
            p05Dps=personal * 0.97,
            p95Dps=personal * 1.03,
            confidence95=None,
            totalDamage=personal * duration,
            fightLength=duration,
            iterations=1,
            targets=request.fight.targets,
            breakdown=breakdown,
            gameVersion=self.settings.game_version,
            simcVersion="n/a",
            simcCommit=str(ruleset_meta.get("simcCommit") or self.settings.data_snapshot_id),
            dataSnapshotId=self.settings.data_snapshot_id,
            clientBuild=ruleset_meta.get("clientBuild"),
            hotfixDate=ruleset_meta.get("hotfixDate"),
            sources=["FastEstimateEngine", "estimate_baselines.json", "ruleset combatRating"],
            engine=self.name,
            isDemo=False,
            isApproximation=True,
            assumptions=assumptions,
            warnings=warnings,
        )


def is_fast_estimate(request: SimulationRequest) -> bool:
    return request.fight.mode in {SimulationMode.fast_estimate}
