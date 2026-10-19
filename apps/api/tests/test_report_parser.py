from pathlib import Path

from app.simulation.report_parser import parse_json2_report

FIXTURE = Path(__file__).parent / "fixtures" / "json2_assassination_excerpt.json"


def test_parse_json2_excerpt_mean_dps() -> None:
    result = parse_json2_report(
        FIXTURE,
        game_version="12.1.5",
        data_snapshot_id="test-snapshot",
        targets=1,
    )
    assert result.meanDps > 0
    assert result.simcVersion == "1210-01"
    assert result.simcCommit
    assert result.breakdown
    assert result.breakdown[0].damage > 0
    assert result.isDemo is False
    assert "SimulationCraft json2" in result.sources[0]
