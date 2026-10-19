from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.domain.models import AbilityBreakdownRow, SimulationResult


def _mean(stat: Any) -> float | None:
    if stat is None:
        return None
    if isinstance(stat, (int, float)):
        return float(stat)
    if isinstance(stat, dict) and "mean" in stat:
        return float(stat["mean"])
    return None


def _percentile(stat: Any, key: str) -> float | None:
    if not isinstance(stat, dict):
        return None
    # SimC json2 may expose q / percentile fields inconsistently across versions.
    for candidate in (key, f"percentile_{key}", f"p{key}"):
        if candidate in stat and stat[candidate] is not None:
            try:
                return float(stat[candidate])
            except (TypeError, ValueError):
                continue
    distribution = stat.get("distribution")
    if isinstance(distribution, list) and distribution:
        # Best-effort: treat as sorted samples if present.
        try:
            values = sorted(float(x) for x in distribution)
            if key in {"05", "5"}:
                idx = max(0, int(len(values) * 0.05) - 1)
                return values[idx]
            if key in {"95"}:
                idx = min(len(values) - 1, int(len(values) * 0.95))
                return values[idx]
        except (TypeError, ValueError):
            return None
    return None


def parse_json2_report(
    report: dict[str, Any] | str | Path,
    *,
    game_version: str,
    data_snapshot_id: str,
    targets: int | None = None,
    engine: str = "simc",
    is_demo: bool = False,
    warnings: list[str] | None = None,
    assumptions: list[str] | None = None,
    personal_dps: float | None = None,
    external_contribution_dps: float | None = None,
    effective_dps: float | None = None,
) -> SimulationResult:
    if isinstance(report, (str, Path)):
        data = json.loads(Path(report).read_text(encoding="utf-8"))
    else:
        data = report

    sim = data.get("sim") or data
    players = sim.get("players") or []
    if not players:
        raise ValueError("json2 report contains no players")

    player = players[0]
    collected = player.get("collected_data") or {}
    dps = collected.get("dps") or {}
    mean_dps = _mean(dps)
    if mean_dps is None or mean_dps <= 0:
        raise ValueError("json2 report missing positive mean DPS")

    total_damage = _mean(collected.get("dmg"))
    fight_length = _mean(collected.get("fight_length"))
    iterations = None
    if isinstance(dps, dict) and "count" in dps:
        iterations = int(dps["count"])

    breakdown: list[AbilityBreakdownRow] = []
    stats = list(player.get("stats") or [])
    for pet_stats in player.get("stats_pets") or []:
        if isinstance(pet_stats, dict) and "stats" in pet_stats:
            stats.extend(pet_stats["stats"] or [])
        elif isinstance(pet_stats, list):
            stats.extend(pet_stats)

    for stat in stats:
        amount = _mean(stat.get("actual_amount") or stat.get("total_amount"))
        if not amount or amount <= 0:
            continue
        casts = _mean(stat.get("num_executes")) or 0.0
        pct = float(stat.get("portion_amount") or 0.0) * 100.0
        portion_aps = stat.get("portion_aps")
        dps_contrib = _mean(portion_aps)
        avg_hit = (amount / casts) if casts else None
        breakdown.append(
            AbilityBreakdownRow(
                name=str(stat.get("name") or "unknown"),
                spellId=stat.get("id"),
                damage=amount,
                pctTotal=pct,
                casts=casts,
                avgHit=avg_hit,
                dps=dps_contrib,
            )
        )

    breakdown.sort(key=lambda row: row.damage, reverse=True)

    action_sequence = None
    seq = collected.get("action_sequence")
    if isinstance(seq, list) and seq:
        action_sequence = seq[:200]

    options = sim.get("options") or {}
    report_targets = targets
    if report_targets is None:
        report_targets = options.get("desired_targets")
    target_count = int(report_targets) if report_targets is not None else None
    dps_per_target = (mean_dps / target_count) if target_count else None

    p05 = _percentile(dps, "05") if isinstance(dps, dict) else None
    if p05 is None and isinstance(dps, dict):
        p05 = _percentile(dps, "5")
    p95 = _percentile(dps, "95") if isinstance(dps, dict) else None

    # Approximate percentiles from mean±1.645σ when distribution missing.
    std = _mean(dps.get("std_dev")) if isinstance(dps, dict) else None
    if p05 is None and std is not None:
        p05 = max(0.0, mean_dps - 1.645 * std)
    if p95 is None and std is not None:
        p95 = mean_dps + 1.645 * std

    return SimulationResult(
        meanDps=mean_dps,
        minDps=_mean(dps.get("min")) if isinstance(dps, dict) else None,
        maxDps=_mean(dps.get("max")) if isinstance(dps, dict) else None,
        medianDps=_mean(dps.get("median")) if isinstance(dps, dict) else None,
        stdDev=std,
        meanStdDev=_mean(dps.get("mean_std_dev")) if isinstance(dps, dict) else None,
        p05Dps=p05,
        p95Dps=p95,
        dpsPerTarget=dps_per_target,
        personalDps=personal_dps if personal_dps is not None else mean_dps,
        externalContributionDps=external_contribution_dps,
        effectiveDps=effective_dps,
        totalDamage=total_damage,
        fightLength=fight_length,
        iterations=iterations or options.get("iterations"),
        targets=target_count,
        breakdown=breakdown,
        actionSequence=action_sequence,
        gameVersion=game_version,
        simcVersion=str(data.get("version") or "unknown"),
        simcCommit=str(data.get("git_revision") or "unknown"),
        dataSnapshotId=data_snapshot_id,
        sources=[
            "SimulationCraft json2",
            f"simc {data.get('version')} ({data.get('git_branch')}/{data.get('git_revision')})",
        ],
        engine=engine,
        isDemo=is_demo,
        warnings=warnings or [],
        assumptions=assumptions or [],
    )
