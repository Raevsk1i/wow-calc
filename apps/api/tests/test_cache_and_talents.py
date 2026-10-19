from app.domain.cache_keys import simulation_cache_key
from app.domain.comparison import compare_results
from app.domain.models import SimulationRequest, SimulationResult
from app.domain.talents import import_talent_string


def test_cache_key_stable() -> None:
    req = SimulationRequest(specId=259)
    a = simulation_cache_key(req, simc_commit="d91a570", data_snapshot_id="snap")
    b = simulation_cache_key(req, simc_commit="d91a570", data_snapshot_id="snap")
    assert a == b
    req2 = SimulationRequest(specId=258)
    c = simulation_cache_key(req2, simc_commit="d91a570", data_snapshot_id="snap")
    assert a != c


def test_talent_import_header() -> None:
    # Shadow priest MID1 hash from profile — may be long; at least parse header bits.
    from pathlib import Path

    profile = Path(__file__).resolve().parents[3] / "packages/game-data/presets/12.1.5/MID1_Priest_Shadow.simc"
    text = profile.read_text(encoding="utf-8")
    talent_line = next(line for line in text.splitlines() if line.startswith("talents="))
    export = talent_line.split("=", 1)[1]
    result = import_talent_string(export)
    assert result.ok is True
    assert result.specId == 258


def test_compare_results_significance() -> None:
    a = SimulationResult(
        meanDps=100000,
        meanStdDev=100,
        stdDev=1000,
        gameVersion="12.1.5",
        simcVersion="x",
        simcCommit="y",
        dataSnapshotId="z",
        engine="simc",
    )
    b = SimulationResult(
        meanDps=100050,
        meanStdDev=100,
        stdDev=1000,
        gameVersion="12.1.5",
        simcVersion="x",
        simcCommit="y",
        dataSnapshotId="z",
        engine="simc",
    )
    cmp = compare_results(job_a_id="a", job_b_id="b", result_a=a, result_b=b)
    assert cmp.significant is False
    assert cmp.absoluteDiff == 50
