from __future__ import annotations

from app.config import Settings, get_settings
from app.simulation.engine import ISimulationEngine
from app.simulation.mock_engine import MockSimulationEngine
from app.simulation.simc_engine import SimulationCraftEngine


def get_engine(settings: Settings | None = None) -> ISimulationEngine:
    settings = settings or get_settings()
    if settings.sim_engine.lower() == "mock":
        return MockSimulationEngine(settings)
    return SimulationCraftEngine(settings)
