from __future__ import annotations

from app.config import Settings
from app.domain.models import (
    AbilityBreakdownRow,
    SimulationMode,
    SimulationRequest,
    SimulationResult,
    Specialization,
)
from app.simulation.engine import ISimulationEngine, ValidationResult
from app.simulation.fast_estimate import FastEstimateEngine


class MockSimulationEngine(ISimulationEngine):
    """Deterministic demo engine — never present results as real SimC output."""

    name = "mock"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._fast = FastEstimateEngine(settings)

    def validate_request(
        self, request: SimulationRequest, spec: Specialization
    ) -> ValidationResult:
        return ValidationResult(ok=True, errors=[], warnings=["Mock engine active"])

    def run(self, request: SimulationRequest, spec: Specialization) -> SimulationResult:
        if request.fight.mode == SimulationMode.fast_estimate:
            result = self._fast.run(request, spec)
            result.engine = self.name
            result.isDemo = True
            result.warnings = [
                "DEMO RESULT — Fast Estimate path under mock engine.",
                *result.warnings,
            ]
            return result

        base = 50_000 + (request.specId or 0) * 100 + request.fight.targets * 1_500
        if request.rotation.disabledActions:
            base = int(base * 0.92)
        mean = float(base)
        return SimulationResult(
            meanDps=mean,
            personalDps=mean,
            minDps=mean * 0.9,
            maxDps=mean * 1.1,
            medianDps=mean,
            stdDev=mean * 0.05,
            meanStdDev=mean * 0.01,
            p05Dps=mean * 0.9,
            p95Dps=mean * 1.1,
            confidence95=[mean - 1.96 * mean * 0.01, mean + 1.96 * mean * 0.01],
            totalDamage=mean * request.fight.duration,
            fightLength=float(request.fight.duration),
            iterations=request.fight.iterations or 100,
            targets=request.fight.targets,
            breakdown=[
                AbilityBreakdownRow(
                    name="demo_filler",
                    spellId=None,
                    damage=mean * request.fight.duration * 0.6,
                    pctTotal=60.0,
                    casts=100,
                    avgHit=mean * 0.01,
                    dps=mean * 0.6,
                ),
                AbilityBreakdownRow(
                    name="demo_spender",
                    spellId=None,
                    damage=mean * request.fight.duration * 0.4,
                    pctTotal=40.0,
                    casts=40,
                    avgHit=mean * 0.02,
                    dps=mean * 0.4,
                ),
            ],
            gameVersion=self.settings.game_version,
            simcVersion="mock",
            simcCommit="mock",
            dataSnapshotId=self.settings.data_snapshot_id,
            sources=["MockSimulationEngine"],
            engine=self.name,
            isDemo=True,
            isApproximation=False,
            warnings=[
                "DEMO RESULT — not a real SimulationCraft simulation.",
                f"Spec={spec.name}",
            ],
        )
