"""IPv4 subnet and interface address allocation for topology plans."""

from __future__ import annotations

import ipaddress
from dataclasses import dataclass

from .models import AddressAssignment, Link, TopologyPlan, TopologyValidationError


@dataclass(frozen=True)
class AddressingResult:
    """Addresses plus the networks allocated to the plan."""

    addresses: list[AddressAssignment]
    networks: list[str]


def allocate_addresses(plan: TopologyPlan, base_network: str) -> AddressingResult:
    """Allocate deterministic IPv4 addresses without overlapping subnets.

    Switch-connected links form one shared LAN domain per connected switch
    segment and receive a /24. Direct links receive a /30. Switch ports do not
    receive IP addresses; routers and PCs in a LAN do. The first router address
    in a LAN is used as the PC gateway.
    """
    base = _parse_base_network(base_network)
    devices = {device.name: device for device in plan.devices}
    switch_names = {device.name for device in plan.devices if device.kind == "switch"}
    domains = _switch_domains(plan.links, switch_names)

    allocations: list[tuple[ipaddress.IPv4Network, list[tuple[str, str]]]] = []
    assigned_networks: list[str] = []
    cursor = int(base.network_address)
    switch_link_keys = {
        _link_key(link)
        for domain_links in domains.values()
        for link in domain_links
    }

    for link in plan.links:
        if _link_key(link) in switch_link_keys:
            continue
        endpoints = [(link.a_device, link.a_interface), (link.b_device, link.b_interface)]
        network, cursor = _allocate_next(base, 30, cursor)
        allocations.append((network, [(device, interface) for device, interface in endpoints if devices[device].kind != "switch"]))
        assigned_networks.append(str(network))

    for domain_links in domains.values():
        endpoint_set: set[tuple[str, str]] = set()
        for link in domain_links:
            endpoint_set.update(((link.a_device, link.a_interface), (link.b_device, link.b_interface)))
        endpoints = sorted(
            [
                (device, interface)
                for device, interface in endpoint_set
                if devices[device].kind != "switch"
            ],
            key=lambda endpoint: (
                devices[endpoint[0]].kind != "router", endpoint[0], endpoint[1]
            ),
        )
        network, cursor = _allocate_next(base, 24, cursor)
        allocations.append((network, endpoints))
        assigned_networks.append(str(network))

    addresses: list[AddressAssignment] = []
    for network, endpoints in allocations:
        hosts = iter(network.hosts())
        endpoint_addresses: dict[tuple[str, str], ipaddress.IPv4Address] = {}
        for endpoint in endpoints:
            try:
                endpoint_addresses[endpoint] = next(hosts)
            except StopIteration as exc:
                raise TopologyValidationError(f"Network {network} has too many endpoints") from exc
        router_addresses = [address for (device, _), address in endpoint_addresses.items() if devices[device].kind == "router"]
        gateway = str(sorted(router_addresses)[0]) if router_addresses else None
        for (device, interface), address in endpoint_addresses.items():
            addresses.append(
                AddressAssignment(
                    device=device,
                    interface=interface,
                    network=str(network),
                    address=str(address),
                    mask=str(network.netmask),
                    gateway=gateway if devices[device].kind == "pc" else None,
                )
            )

    return AddressingResult(addresses=addresses, networks=assigned_networks)


def _parse_base_network(value: str) -> ipaddress.IPv4Network:
    try:
        network = ipaddress.ip_network(value, strict=False)
    except ValueError as exc:
        raise TopologyValidationError(f"Invalid base network {value!r}: {exc}") from exc
    if not isinstance(network, ipaddress.IPv4Network):
        raise TopologyValidationError("Only IPv4 base networks are supported")
    if network.prefixlen > 30:
        raise TopologyValidationError("Base network must be at least /30")
    return network


def _allocate_next(
    base: ipaddress.IPv4Network, prefix: int, cursor: int
) -> tuple[ipaddress.IPv4Network, int]:
    block_size = 1 << (32 - prefix)
    start = ((cursor + block_size - 1) // block_size) * block_size
    end = start + block_size - 1
    if start < int(base.network_address) or end > int(base.broadcast_address):
        raise TopologyValidationError(
            f"Base network {base} does not have enough space for a /{prefix} subnet"
        )
    return ipaddress.ip_network(f"{ipaddress.IPv4Address(start)}/{prefix}"), end + 1


def _link_key(link: Link) -> tuple[str, str, str, str]:
    return (link.a_device, link.a_interface, link.b_device, link.b_interface)


def _switch_domains(
    links: list[Link], switch_names: set[str]
) -> dict[str, list[Link]]:
    """Group links attached to the same connected switch segment."""
    switch_links = [
        link for link in links if link.a_device in switch_names or link.b_device in switch_names
    ]
    parent: dict[str, str] = {}

    def find(name: str) -> str:
        parent.setdefault(name, name)
        while parent[name] != name:
            parent[name] = parent[parent[name]]
            name = parent[name]
        return name

    def union(left: str, right: str) -> None:
        left_root, right_root = find(left), find(right)
        if left_root != right_root:
            parent[right_root] = left_root

    for link in switch_links:
        union(link.a_device, link.b_device)

    grouped: dict[str, list[Link]] = {}
    for link in switch_links:
        grouped.setdefault(find(link.a_device), []).append(link)
    return grouped
