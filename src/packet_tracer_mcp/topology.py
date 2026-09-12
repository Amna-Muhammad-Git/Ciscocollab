"""Deterministic physical topology planner for the first lab version."""

from __future__ import annotations

from dataclasses import dataclass

from .models import Device, Link, TopologyPlan, TopologyValidationError


@dataclass(frozen=True)
class TopologyRequest:
    """Validated inputs accepted by the topology planner."""

    routers: int = 2
    switches: int = 1
    pcs: int = 2
    routing_protocol: str = "ospf"
    base_network: str = "192.168.0.0/16"

    def __post_init__(self) -> None:
        for field_name in ("routers", "switches", "pcs"):
            value = getattr(self, field_name)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise TopologyValidationError(f"{field_name} must be a non-negative integer")
        if self.routers + self.switches + self.pcs == 0:
            raise TopologyValidationError("At least one device is required")
        protocol = self.routing_protocol.strip().lower()
        if protocol not in TopologyPlan.ALLOWED_ROUTING_PROTOCOLS:
            raise TopologyValidationError(
                f"Unsupported routing protocol {protocol!r}; "
                f"choose one of {sorted(TopologyPlan.ALLOWED_ROUTING_PROTOCOLS)}"
            )
        if not isinstance(self.base_network, str) or not self.base_network.strip():
            raise TopologyValidationError("base_network must be a non-empty string")
        object.__setattr__(self, "routing_protocol", protocol)
        object.__setattr__(self, "base_network", self.base_network.strip())


def build_topology(request: TopologyRequest) -> TopologyPlan:
    """Build a repeatable, connected physical topology.

    Layout rules for this first version:
    - Routers are connected in a chain when there are multiple routers.
    - If switches exist, each router connects to a switch and PCs connect to
      switches in round-robin order.
    - Without switches, PCs connect to the first router.
    - IP addresses are intentionally left empty for Chunk 3.
    """
    devices: list[Device] = []
    for index in range(1, request.routers + 1):
        devices.append(Device(f"R{index}", "router", "2911"))
    for index in range(1, request.switches + 1):
        devices.append(Device(f"SW{index}", "switch", "2960"))
    for index in range(1, request.pcs + 1):
        devices.append(Device(f"PC{index}", "pc", "PC-PT"))

    device_map = {device.name: device for device in devices}
    links: list[Link] = []
    interface_counts: dict[str, int] = {device.name: 0 for device in devices}

    def connect(a_device: str, b_device: str) -> None:
        a_interface = _next_interface(device_map[a_device], interface_counts)
        b_interface = _next_interface(device_map[b_device], interface_counts)
        links.append(Link(a_device, a_interface, b_device, b_interface))

    router_names = [f"R{index}" for index in range(1, request.routers + 1)]
    switch_names = [f"SW{index}" for index in range(1, request.switches + 1)]

    for left, right in zip(router_names, router_names[1:]):
        connect(left, right)

    if switch_names:
        for index, router_name in enumerate(router_names):
            connect(router_name, switch_names[index % len(switch_names)])
        for index in range(1, request.pcs + 1):
            connect(f"PC{index}", switch_names[(index - 1) % len(switch_names)])
    elif router_names:
        for index in range(1, request.pcs + 1):
            connect(f"PC{index}", router_names[(index - 1) % len(router_names)])
    elif switch_names:
        for index in range(1, request.pcs + 1):
            connect(f"PC{index}", switch_names[(index - 1) % len(switch_names)])

    notes = [
        f"Address allocation is reserved for the IP planning stage; requested base network: {request.base_network}.",
        "Interfaces and links are generated deterministically so the same request produces the same lab.",
    ]
    return TopologyPlan(
        devices=devices,
        links=links,
        routing_protocol=request.routing_protocol,
        notes=notes,
    )


def _next_interface(device: Device, counts: dict[str, int]) -> str:
    """Allocate the next Packet Tracer-style interface and record it."""
    index = counts[device.name]
    if device.kind == "router":
        interface = f"GigabitEthernet0/{index}"
    elif device.kind == "switch":
        interface = f"GigabitEthernet0/{index + 1}"
    elif device.kind == "pc":
        if index > 0:
            raise TopologyValidationError(f"PC {device.name} cannot have more than one link")
        interface = "FastEthernet0"
    else:
        interface = f"GigabitEthernet0/{index}"
    device.interfaces.append(interface)
    counts[device.name] += 1
    return interface
