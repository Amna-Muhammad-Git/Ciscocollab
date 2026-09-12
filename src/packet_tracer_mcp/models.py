"""Canonical topology model shared by all Packet Tracer MCP tools."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar


class TopologyValidationError(ValueError):
    """Raised when a topology plan is structurally inconsistent."""


@dataclass
class Device:
    """A physical or virtual device in the lab."""

    name: str
    kind: str
    model: str
    interfaces: list[str] = field(default_factory=list)
    description: str | None = None

    ALLOWED_KINDS: ClassVar[frozenset[str]] = frozenset({"router", "switch", "pc", "server"})

    def __post_init__(self) -> None:
        self.name = _required_text(self.name, "device name")
        self.kind = _required_text(self.kind, "device kind").lower()
        self.model = _required_text(self.model, "device model")
        self.interfaces = _unique_texts(self.interfaces, "device interfaces")
        if self.kind not in self.ALLOWED_KINDS:
            raise TopologyValidationError(f"Unsupported device kind {self.kind!r}")


@dataclass
class Link:
    """A point-to-point connection between two device interfaces."""

    a_device: str
    a_interface: str
    b_device: str
    b_interface: str
    medium: str = "copper"

    def __post_init__(self) -> None:
        self.a_device = _required_text(self.a_device, "link endpoint device")
        self.a_interface = _required_text(self.a_interface, "link endpoint interface")
        self.b_device = _required_text(self.b_device, "link endpoint device")
        self.b_interface = _required_text(self.b_interface, "link endpoint interface")
        self.medium = _required_text(self.medium, "link medium").lower()
        if (self.a_device, self.a_interface) == (self.b_device, self.b_interface):
            raise TopologyValidationError("A link cannot connect an interface to itself")


@dataclass
class AddressAssignment:
    """An IP address assigned to a device interface."""

    device: str
    interface: str
    network: str
    address: str
    mask: str
    gateway: str | None = None

    def __post_init__(self) -> None:
        self.device = _required_text(self.device, "address device")
        self.interface = _required_text(self.interface, "address interface")
        self.network = _required_text(self.network, "address network")
        self.address = _required_text(self.address, "address")
        self.mask = _required_text(self.mask, "address mask")
        if self.gateway is not None:
            self.gateway = _required_text(self.gateway, "address gateway")


@dataclass
class Vlan:
    """A VLAN definition used by one or more switch ports."""

    vlan_id: int
    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.vlan_id, int) or isinstance(self.vlan_id, bool):
            raise TopologyValidationError("VLAN ID must be an integer")
        if not 1 <= self.vlan_id <= 4094:
            raise TopologyValidationError("VLAN ID must be between 1 and 4094")
        self.name = _required_text(self.name, "VLAN name")


@dataclass
class TopologyPlan:
    """The canonical, JSON-compatible representation of a lab."""

    devices: list[Device] = field(default_factory=list)
    links: list[Link] = field(default_factory=list)
    addresses: list[AddressAssignment] = field(default_factory=list)
    vlans: list[Vlan] = field(default_factory=list)
    routing_protocol: str = "none"
    notes: list[str] = field(default_factory=list)

    ALLOWED_ROUTING_PROTOCOLS: ClassVar[frozenset[str]] = frozenset({"none", "static", "ospf"})

    def __post_init__(self) -> None:
        self.routing_protocol = _required_text(self.routing_protocol, "routing protocol").lower()
        self.notes = _unique_texts(self.notes, "plan notes")
        if self.routing_protocol not in self.ALLOWED_ROUTING_PROTOCOLS:
            raise TopologyValidationError(f"Unsupported routing protocol {self.routing_protocol!r}")
        self.validate()

    def validate(self) -> None:
        """Validate references and uniqueness across the complete plan."""
        device_names = [device.name for device in self.devices]
        _ensure_unique(device_names, "device names")
        device_map = {device.name: device for device in self.devices}
        _ensure_unique([vlan.vlan_id for vlan in self.vlans], "VLAN IDs")

        used_interfaces: set[tuple[str, str]] = set()
        for link in self.links:
            for device_name, interface_name in ((link.a_device, link.a_interface), (link.b_device, link.b_interface)):
                device = device_map.get(device_name)
                if device is None:
                    raise TopologyValidationError(f"Link references unknown device {device_name!r}")
                if interface_name not in device.interfaces:
                    raise TopologyValidationError(f"Link references unknown interface {device_name}:{interface_name}")
                endpoint = (device_name, interface_name)
                if endpoint in used_interfaces:
                    raise TopologyValidationError(f"Interface {device_name}:{interface_name} is used by more than one link")
                used_interfaces.add(endpoint)

        assigned_interfaces: set[tuple[str, str]] = set()
        for assignment in self.addresses:
            device = device_map.get(assignment.device)
            if device is None:
                raise TopologyValidationError(f"Address assignment references unknown device {assignment.device!r}")
            if assignment.interface not in device.interfaces:
                raise TopologyValidationError(f"Address assignment references unknown interface {assignment.device}:{assignment.interface}")
            endpoint = (assignment.device, assignment.interface)
            if endpoint in assigned_interfaces:
                raise TopologyValidationError(f"Interface {assignment.device}:{assignment.interface} has more than one address")
            assigned_interfaces.add(endpoint)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TopologyPlan":
        if not isinstance(data, dict):
            raise TopologyValidationError("A topology plan must be a JSON object")
        try:
            return cls(
                devices=[Device(**item) for item in data.get("devices", [])],
                links=[Link(**item) for item in data.get("links", [])],
                addresses=[AddressAssignment(**item) for item in data.get("addresses", [])],
                vlans=[Vlan(**item) for item in data.get("vlans", [])],
                routing_protocol=data.get("routing_protocol", "none"),
                notes=data.get("notes", []),
            )
        except TypeError as exc:
            raise TopologyValidationError(f"Invalid topology field: {exc}") from exc


def _required_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TopologyValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


def _unique_texts(values: list[str], field_name: str) -> list[str]:
    if not isinstance(values, list):
        raise TopologyValidationError(f"{field_name} must be a list")
    cleaned = [_required_text(value, field_name) for value in values]
    _ensure_unique(cleaned, field_name)
    return cleaned


def _ensure_unique(values: list[Any], field_name: str) -> None:
    if len(values) != len(set(values)):
        raise TopologyValidationError(f"Duplicate values found in {field_name}")
