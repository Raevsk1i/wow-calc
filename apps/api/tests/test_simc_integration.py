from pathlib import Path

import pytest

from app.config import Settings
from app.data.catalog import get_spec
from app.domain.models import FightConfig, SimulationMode, SimulationRequest
from app.simulation.simc_engine import SimulationCraftEngine

REPO = Path(__file__).resolve().parents[3]
SIMC = REPO / "engine/simc/bin/simc"


@pytest.mark.skipif(not SIMC.is_file(), reason="SimulationCraft binary not built")
def test_shadow_priest_real_sim() -> None:
    settings = Settings(
        sim_engine="simc",
        simc_path=str(SIMC),
        simc_profiles_dir=str(REPO / "packages/game-data/presets/12.1.5"),
        game_data_dir=str(REPO / "packages/game-data"),
        sim_timeout_seconds=120,
        max_iterations_quick=20,
        simc_threads=2,
    )
    engine = SimulationCraftEngine(settings)
    spec = get_spec(258)
    assert spec is not None
    request = SimulationRequest(
        specId=258,
        fight=FightConfig(targets=1, duration=120, mode=SimulationMode.quick, iterations=20),
    )
    result = engine.run(request, spec)
    assert result.meanDps > 0
    assert result.engine == "simc"
    assert result.isDemo is False
    assert result.breakdown
