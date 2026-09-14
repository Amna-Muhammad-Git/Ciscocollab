"""Plan-only Packet Tracer backend.

Packet Tracer has no supported external deployment API in this project, so its
backend deliberately generates guidance only and never controls the desktop.
"""

from __future__ import annotations

from typing import Any

from ..configs import generate_configurations
from ..diagrams import render_mermaid
from ..models import TopologyPlan
from .base import BackendCapabilities, BackendOperation, LabBackend


class PacketTracerBackend(LabBackend):
    name = "packet_tracer"
    capabilities = BackendCapabilities(
        operations=frozenset({BackendOperation.GENERATE, BackendOperation.TEST})
    )

    def generate(self, plan: TopologyPlan) -> dict[str, Any]:
        return {
            "backend": self.name,
            "configurations": generate_configurations(plan),
            "diagram": render_mermaid(plan),
            "manual_steps": [
                "Place the devices in Packet Tracer.",
                "Connect the cables according to the diagram.",
                "Paste the generated router and switch configurations.",
                "Enter the PC IP settings manually.",
            ],
        }

