"""Containerlab topology-file generation backend."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from ..models import Device, TopologyPlan, TopologyValidationError
from .base import BackendCapabilities, BackendOperation, LabBackend


@dataclass(frozen=True)
class ContainerlabProfile:
    """Container images used when translating device types to containerlab."""

    router_image: str = "frrouting/frr:latest"
    switch_image: str = "wbitt/network-multitool:latest"
    pc_image: str = "wbitt/network-multitool:latest"
    server_image: str = "wbitt/network-multitool:latest"
    node_kind: str = "linux"

    PROFILE_NAME: str = "frr-free"

    def __post_init__(self) -> None:
        for field_name in (
            "router_image",
            "switch_image",
            "pc_image",
            "server_image",
            "node_kind",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string")
        for image in (self.router_image, self.switch_image, self.pc_image, self.server_image):
            if any(character in image for character in "\n\r\t"):
                raise ValueError("Container image references cannot contain whitespace control characters")

    @classmethod
    def free_frr(cls) -> "ContainerlabProfile":
        """Return the initial no-license profile for local experimentation."""
        return cls(
            router_image="frrouting/frr:latest",
            switch_image="wbitt/network-multitool:latest",
            pc_image="wbitt/network-multitool:latest",
            server_image="wbitt/network-multitool:latest",
        )

    def image_for(self, device: Device) -> str:
        images = {
            "router": self.router_image,
            "switch": self.switch_image,
            "pc": self.pc_image,
            "server": self.server_image,
        }
        return images[device.kind]

    def describe(self) -> dict[str, str]:
        return {
            "name": self.PROFILE_NAME,
            "router_image": self.router_image,
            "switch_image": self.switch_image,
            "pc_image": self.pc_image,
            "server_image": self.server_image,
            "switch_note": "The initial profile uses a Linux networking container as a switch placeholder.",
        }


class ContainerlabBackend(LabBackend):
    """Generate containerlab YAML without deploying it."""

    name = "containerlab"
    capabilities = BackendCapabilities(
        operations=frozenset({BackendOperation.GENERATE})
    )

    def __init__(self, profile: ContainerlabProfile | None = None) -> None:
        self.profile = profile or ContainerlabProfile.free_frr()

    def generate(self, plan: TopologyPlan) -> dict[str, Any]:
        topology = generate_containerlab_yaml(plan, self.profile)
        return {
            "status": "ok",
            "backend": self.name,
            "format": "containerlab-yaml",
            "filename": f"{topology['name']}.clab.yml",
            "topology": topology["yaml"],
            "node_interfaces": topology["node_interfaces"],
            "warnings": topology["warnings"],
        }


def generate_containerlab_yaml(
    plan: TopologyPlan,
    profile: ContainerlabProfile | None = None,
    lab_name: str = "packet-tracer-lab",
) -> dict[str, Any]:
    """Translate a plan into deterministic containerlab YAML text."""
    profile = profile or ContainerlabProfile.free_frr()
    name = _safe_lab_name(lab_name)
    node_interfaces: dict[str, dict[str, str]] = {}
    warnings: list[str] = []
    lines = [f"name: {_yaml_string(name)}", "", "topology:", "  nodes:"]

    for device in plan.devices:
        node_name = _node_name(device.name)
        interface_map = {
            interface: f"eth{index}"
            for index, interface in enumerate(device.interfaces, start=1)
        }
        node_interfaces[device.name] = interface_map
        lines.extend(
            [
                f"    {node_name}:",
                f"      kind: {_yaml_string(profile.node_kind)}",
                f"      image: {_yaml_string(profile.image_for(device))}",
            ]
        )
        if device.kind == "switch":
            warnings.append(
                f"{device.name} uses a Linux container placeholder; a real L2 switch image or bridge configuration is needed."
            )
        if device.kind == "pc":
            warnings.append(
                f"{device.name} uses a network-multitool container placeholder for host testing."
            )

    lines.extend(["", "  links:"])
    for link in plan.links:
        try:
            a_endpoint = f"{_node_name(link.a_device)}:{node_interfaces[link.a_device][link.a_interface]}"
            b_endpoint = f"{_node_name(link.b_device)}:{node_interfaces[link.b_device][link.b_interface]}"
        except KeyError as exc:
            raise TopologyValidationError(
                f"Could not map link endpoint in containerlab output: {exc}"
            ) from exc
        lines.append(f"    - endpoints: [{_yaml_string(a_endpoint)}, {_yaml_string(b_endpoint)}]")

    return {
        "name": name,
        "yaml": "\n".join(lines) + "\n",
        "node_interfaces": node_interfaces,
        "warnings": warnings,
    }


def _node_name(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower())
    if not value or not re.match(r"^[a-zA-Z]", value):
        value = f"node-{value}"
    return value


def _safe_lab_name(name: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9_-]", "-", name.strip().lower()).strip("-")
    if not value:
        raise ValueError("lab_name must contain at least one letter or number")
    return value


def _yaml_string(value: str) -> str:
    escaped = value.replace("'", "''")
    return f"'{escaped}'"
