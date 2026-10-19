from __future__ import annotations

from app.config import Settings
from app.domain.models import (
    AbilityBreakdownRow,
    Role,
    SimulationRequest,
    SimulationResult,
    Specialization,
)
from app.simulation.engine import ISimulationEngine, ValidationResult
from app.simulation.profile_composer import compute_augmentation_contribution


class MockSimulationEngine(ISimulationEngine):
    """Deterministic demo engine — never present results as real SimC output."""

    name = "mock"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def validate_request(
        self, request: SimulationRequest, spec: Specialization
    ) -> ValidationResult:
        return ValidationResult(ok=True, errors=[], warnings=["Mock engine active"])

    def run(self, request: SimulationRequest, spec: Specialization) -> SimulationResult:
        base = 50_000 + request.specId * 100 + request.fight.targets * 1_500
        if request.rotation.disabledActions:
            base = int(base * 0.92)
        if request.raid and not request.raid.battleShout:
            base = int(base * 0.97)
        mean = float(base)
        personal = mean
        assumptions = [
            f"Encounter: {request.fight.fightStyle.value}, {request.fight.targets} target(s), "
            f"{request.fight.duration}s.",
            f"Simulation mode={request.fight.mode.value}.",
        ]
        warnings = [
            "DEMO RESULT — not a real SimulationCraft simulation.",
            f"Spec={spec.name} ({spec.canonicalId or spec.id})",
        ]

        if spec.role == Role.healer:
            profile = request.healerDamageProfile
            activity = profile.damageActivity if profile else 1.0
            personal = mean * activity
            mean = personal
            assumptions.append(f"Healer damageActivity={activity:.2f}.")

        external = None
        effective = None
        if spec.role == Role.support:
            external, effective, w, a = compute_augmentation_contribution(personal, request, spec)
            warnings.extend(w)
            assumptions.extend(a)
            if external is None:
                assumptions.append("Augmentation: Personal DPS only.")

        if spec.role == Role.tank:
            assumptions.append("Tank offensive_tank mock (incomingDamageModel not simulated).")

        std = mean * 0.05
        return SimulationResult(
            meanDps=mean,
            minDps=mean * 0.9,
            maxDps=mean * 1.1,
            medianDps=mean,
            stdDev=std,
            meanStdDev=mean * 0.01,
            p05Dps=mean - 1.645 * std,
            p95Dps=mean + 1.645 * std,
            dpsPerTarget=mean / max(1, request.fight.targets),
            personalDps=personal,
            externalContributionDps=external,
            effectiveDps=effective,
            totalDamage=mean * request.fight.duration,
            fightLength=float(request.fight.duration),
            iterations=request.fight.iterations
            or (1000 if request.fight.mode.is_final() else 100),
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
            warnings=warnings,
            assumptions=assumptions,
        )
