from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.domain.models import SimulationRequest, SimulationResult, Specialization


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str]
    warnings: list[str]


class ISimulationEngine(ABC):
    name: str

    @abstractmethod
    def validate_request(
        self, request: SimulationRequest, spec: Specialization
    ) -> ValidationResult:
        raise NotImplementedError

    @abstractmethod
    def run(self, request: SimulationRequest, spec: Specialization) -> SimulationResult:
        raise NotImplementedError
