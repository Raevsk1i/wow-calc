from app.config import get_settings
from app.data.catalog import clear_catalog_cache, get_spec_by_key
from app.domain.models import FightConfig, SimulationMode, SimulationRequest
from app.simulation.fast_estimate import FastEstimateEngine


def test_fast_estimate_scales_with_targets() -> None:
    clear_catalog_cache()
    get_settings.cache_clear()
    engine = FastEstimateEngine(get_settings())
    spec = get_spec_by_key("demon_hunter_devourer")
    assert spec is not None
    st = engine.run(
        SimulationRequest(
            specKey="demon_hunter_devourer",
            fight=FightConfig(targets=1, duration=300, mode=SimulationMode.fast_estimate),
        ),
        spec,
    )
    aoe = engine.run(
        SimulationRequest(
            specKey="demon_hunter_devourer",
            fight=FightConfig(targets=5, duration=300, mode=SimulationMode.fast_estimate),
        ),
        spec,
    )
    assert st.isApproximation is True
    assert aoe.meanDps > st.meanDps
    clear_catalog_cache()
