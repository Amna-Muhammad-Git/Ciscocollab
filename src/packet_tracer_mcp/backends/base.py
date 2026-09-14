"""Common contract for Packet Tracer and automated simulator backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

from ..models import TopologyPlan


class BackendError(RuntimeError):
    """Base error raised by a simulator backend."""


class OperationRisk(str, Enum):
    """Safety classification for backend operations."""

    READ_ONLY = "read_only"
    CHANGES_STATE = "changes_state"
    DESTRUCTIVE = "destructive"


class BackendOperation(str, Enum):
    """Operations that a simulator backend may support."""

    GENERATE = "generate"
    DEPLOY = "deploy"
    INSPECT = "inspect"
    CONFIGURE = "configure"
    TEST = "test"
    SAVE = "save"
    DESTROY = "destroy"


@dataclass(frozen=True)
class BackendCapabilities:
    """Advertised backend features and their safety policy."""

    operations: frozenset[BackendOperation]

    def supports(self, operation: BackendOperation) -> bool:
        return operation in self.operations


OPERATION_RISK: dict[BackendOperation, OperationRisk] = {
    BackendOperation.GENERATE: OperationRisk.READ_ONLY,
    BackendOperation.INSPECT: OperationRisk.READ_ONLY,
    BackendOperation.TEST: OperationRisk.READ_ONLY,
    BackendOperation.DEPLOY: OperationRisk.CHANGES_STATE,
    BackendOperation.CONFIGURE: OperationRisk.CHANGES_STATE,
    BackendOperation.SAVE: OperationRisk.CHANGES_STATE,
    BackendOperation.DESTROY: OperationRisk.DESTRUCTIVE,
}


class LabBackend(ABC):
    """Interface every simulator backend must implement."""

    name: str
    capabilities: BackendCapabilities

    @abstractmethod
    def generate(self, plan: TopologyPlan) -> dict[str, Any]:
        """Generate simulator-specific artifacts without changing external state."""

    def deploy(self, plan: TopologyPlan) -> dict[str, Any]:
        return self._unsupported(BackendOperation.DEPLOY)

    def inspect(self, lab_name: str) -> dict[str, Any]:
        return self._unsupported(BackendOperation.INSPECT)

    def configure(self, lab_name: str, configurations: dict[str, str]) -> dict[str, Any]:
        return self._unsupported(BackendOperation.CONFIGURE)

    def test(self, lab_name: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
        return self._unsupported(BackendOperation.TEST)

    def save(self, lab_name: str) -> dict[str, Any]:
        return self._unsupported(BackendOperation.SAVE)

    def destroy(self, lab_name: str, *, confirmed: bool = False) -> dict[str, Any]:
        if not confirmed:
            raise BackendError("Destroying a lab requires explicit confirmation")
        return self._unsupported(BackendOperation.DESTROY)

    def _unsupported(self, operation: BackendOperation) -> dict[str, Any]:
        if not self.capabilities.supports(operation):
            raise BackendError(f"Backend {self.name!r} does not support {operation.value}")
        raise NotImplementedError(f"Backend {self.name!r} has not implemented {operation.value}")

