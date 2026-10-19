from __future__ import annotations

import shutil

from app.config import Settings
from app.domain.models import SimulationRequest, SimulationResult, SimulationSupport, Specialization
from app.simulation.engine import ISimulationEngine, ValidationResult
from app.simulation.profile_composer import compose_profile, profile_without_talents_hash
from app.simulation.report_parser import parse_json2_report
from app.simulation.sandbox import SimulationCraftError, run_simc


class SimulationCraftEngine(ISimulationEngine):
    name = "simc"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def validate_request(
        self, request: SimulationRequest, spec: Specialization
    ) -> ValidationResult:
        errors: list[str] = []
        warnings: list[str] = []

        if request.gameVersion != self.settings.game_version:
            errors.append(
                f"Unsupported gameVersion {request.gameVersion}; pinned {self.settings.game_version}"
            )
        if spec.simulationSupport == SimulationSupport.unsupported:
            errors.append(f"{spec.name} is unsupported for DPS simulation on this engine pin")
        if not spec.presetProfile:
            errors.append("Specialization is missing a SimulationCraft preset profile")
        if request.fight.targets < 1 or request.fight.targets > self.settings.max_targets:
            errors.append("Invalid target count")
        if (
            request.fight.duration < self.settings.min_fight_duration
            or request.fight.duration > self.settings.max_fight_duration
        ):
            errors.append("Invalid fight duration")
        if spec.simulationSupport == SimulationSupport.experimental:
            warnings.append("Experimental specialization model")

        return ValidationResult(ok=not errors, errors=errors, warnings=warnings)

    def run(self, request: SimulationRequest, spec: Specialization) -> SimulationResult:
        validation = self.validate_request(request, spec)
        if not validation.ok:
            raise ValueError("; ".join(validation.errors))

        composed = compose_profile(
            request,
            settings=self.settings,
            preset_filename=spec.presetProfile or "",
            support=spec.simulationSupport,
            default_hero_talent=spec.defaultHeroTalent,
        )
        warnings = [*validation.warnings, *composed.warnings]

        try:
            run = run_simc(
                simc_path=self.settings.simc_path,
                profile_text=composed.text,
                extra_args=composed.extra_args,
                timeout_seconds=self.settings.sim_timeout_seconds,
            )
        except SimulationCraftError as exc:
            # Retry once without talents= hash when init fails (known MID1 pin issue).
            if "Initialization error" in (exc.stderr or "") and "talents=" in composed.text:
                retry_text = profile_without_talents_hash(
                    composed.text, request.talents.heroTalent or spec.defaultHeroTalent
                )
                warnings.append(
                    "Initial profile failed talent init; retried without talents= hash "
                    f"(hero_talents={request.talents.heroTalent or spec.defaultHeroTalent})."
                )
                run = run_simc(
                    simc_path=self.settings.simc_path,
                    profile_text=retry_text,
                    extra_args=composed.extra_args,
                    timeout_seconds=self.settings.sim_timeout_seconds,
                )
            else:
                raise ValueError(str(exc) + (f": {exc.stderr[-500:]}" if exc.stderr else "")) from exc

        try:
            result = parse_json2_report(
                run.report_path,
                game_version=self.settings.game_version,
                data_snapshot_id=self.settings.data_snapshot_id,
                targets=request.fight.targets,
                engine=self.name,
                is_demo=False,
                warnings=warnings,
            )
        finally:
            shutil.rmtree(run.work_dir, ignore_errors=True)

        return result
