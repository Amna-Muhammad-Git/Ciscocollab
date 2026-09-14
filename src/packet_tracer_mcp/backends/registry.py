"""Safe registry for selecting simulator backends."""

from __future__ import annotations

from .base import BackendError, LabBackend


class BackendRegistry:
    """Name-based backend registry with duplicate protection."""

    def __init__(self) -> None:
        self._backends: dict[str, LabBackend] = {}

    def register(self, backend: LabBackend) -> None:
        name = backend.name.strip().lower()
        if not name:
            raise BackendError("Backend name must be non-empty")
        if name in self._backends:
            raise BackendError(f"Backend {name!r} is already registered")
        self._backends[name] = backend

    def get(self, name: str) -> LabBackend:
        key = name.strip().lower()
        try:
            return self._backends[key]
        except KeyError as exc:
            available = ", ".join(sorted(self._backends)) or "none"
            raise BackendError(f"Unknown backend {name!r}; available: {available}") from exc

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._backends))

