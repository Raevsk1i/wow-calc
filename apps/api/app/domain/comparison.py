from __future__ import annotations

from app.domain.models import ComparisonResult, SimulationResult


def compare_results(
    *,
    job_a_id: str,
    job_b_id: str,
    result_a: SimulationResult,
    result_b: SimulationResult,
) -> ComparisonResult:
    dps_a = result_a.meanDps
    dps_b = result_b.meanDps
    absolute = dps_b - dps_a
    percent = (absolute / dps_a * 100.0) if dps_a else 0.0

    # Conservative significance: difference should exceed combined mean_std_dev-like error.
    err_a = result_a.meanStdDev or result_a.stdDev or 0.0
    err_b = result_b.meanStdDev or result_b.stdDev or 0.0
    threshold = (err_a + err_b) * 2 if (err_a or err_b) else abs(dps_a) * 0.01
    significant = abs(absolute) > threshold

    by_name_a = {row.name: row for row in result_a.breakdown}
    by_name_b = {row.name: row for row in result_b.breakdown}
    names = sorted(set(by_name_a) | set(by_name_b))
    breakdown_diff = []
    for name in names:
        a = by_name_a.get(name)
        b = by_name_b.get(name)
        damage_a = a.damage if a else 0.0
        damage_b = b.damage if b else 0.0
        breakdown_diff.append(
            {
                "name": name,
                "damageA": damage_a,
                "damageB": damage_b,
                "absoluteDiff": damage_b - damage_a,
            }
        )
    breakdown_diff.sort(key=lambda row: abs(row["absoluteDiff"]), reverse=True)

    note = (
        "Difference exceeds estimated error band."
        if significant
        else "Difference is within estimated error band; do not treat as a reliable upgrade."
    )

    return ComparisonResult(
        jobAId=job_a_id,
        jobBId=job_b_id,
        dpsA=dps_a,
        dpsB=dps_b,
        absoluteDiff=absolute,
        percentDiff=percent,
        significant=significant,
        note=note,
        breakdownDiff=breakdown_diff[:40],
    )
