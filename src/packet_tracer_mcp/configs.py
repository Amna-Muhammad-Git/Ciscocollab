"""Cisco IOS and Packet Tracer host configuration rendering."""

from __future__ import annotations

import ipaddress
from collections import defaultdict, deque

from .models import AddressAssignment, Device, Link, TopologyPlan, TopologyValidationError


def generate_configurations(plan: TopologyPlan) -> dict:
    """Render device-specific configuration from a validated topology plan."""
    devices = {device.name: device for device in plan.devices}
    addresses = _addresses_by_device(plan.addresses)
    links_by_endpoint = _links_by_endpoint(plan.links)
    result: list[dict] = []
    warnings: list[str] = []

    for device in plan.devices:
        if device.kind == "router":
            config = _router_config(device, plan, addresses, links_by_endpoint, devices)
            result.append({"name": device.name, "kind": device.kind, "model": device.model, "config": config})
        elif device.kind == "switch":
            config = _switch_config(device, plan, links_by_endpoint)
            result.append({"name": device.name, "kind": device.kind, "model": device.model, "config": config})
        elif device.kind == "pc":
            host = _pc_settings(device, addresses)
            if host is None:
                warnings.append(f"{device.name} has no IP assignment")
            result.append({"name": device.name, "kind": device.kind, "model": device.model, "host_settings": host})

    return {"status": "ok", "devices": result, "warnings": warnings}


def _router_config(
    device: Device,
    plan: TopologyPlan,
    addresses: dict[str, list[AddressAssignment]],
    links_by_endpoint: dict[tuple[str, str], Link],
    devices: dict[str, Device],
) -> str:
    lines = ["enable", "configure terminal", "no ip domain-lookup", f"hostname {device.name}"]
    for interface in device.interfaces:
        lines.extend([f"interface {interface}"])
        link = links_by_endpoint.get((device.name, interface))
        if link:
            peer_device, peer_interface = _peer(link, device.name, interface)
            lines.append(f" description Link to {peer_device} {peer_interface}")
        assignment = next((item for item in addresses.get(device.name, []) if item.interface == interface), None)
        if assignment:
            lines.extend([f" ip address {assignment.address} {assignment.mask}", " no shutdown"])
        else:
            lines.append(" shutdown")
        lines.append(" exit")

    if plan.routing_protocol == "ospf":
        lines.extend(["router ospf 1", f" router-id {_router_id(device.name)}"])
        for assignment in addresses.get(device.name, []):
            lines.append(f" network {assignment.network.split('/')[0]} {_wildcard(assignment.mask)} area 0")
        lines.append(" exit")
    elif plan.routing_protocol == "static":
        lines.extend(_static_routes(device.name, plan, addresses, devices))
    lines.extend(["end", "write memory"])
    return "\n".join(lines)


def _switch_config(device: Device, plan: TopologyPlan, links_by_endpoint: dict[tuple[str, str], Link]) -> str:
    lines = ["enable", "configure terminal", "no ip domain-lookup", f"hostname {device.name}"]
    for vlan in plan.vlans:
        lines.extend([f"vlan {vlan.vlan_id}", f" name {vlan.name}", " exit"])
    for interface in device.interfaces:
        lines.extend([f"interface {interface}"])
        link = links_by_endpoint.get((device.name, interface))
        if link:
            peer_device, peer_interface = _peer(link, device.name, interface)
            lines.append(f" description Link to {peer_device} {peer_interface}")
            lines.append(" switchport mode access")
        lines.extend([" no shutdown", " exit"])
    lines.extend(["end", "write memory"])
    return "\n".join(lines)


def _pc_settings(device: Device, addresses: dict[str, list[AddressAssignment]]) -> dict | None:
    assignment = addresses.get(device.name, [None])[0]
    if assignment is None:
        return None
    return {
        "interface": assignment.interface,
        "ip_address": assignment.address,
        "subnet_mask": assignment.mask,
        "default_gateway": assignment.gateway,
        "instructions": "Packet Tracer: Desktop > IP Configuration > enter these values.",
    }


def _static_routes(device_name: str, plan: TopologyPlan, addresses: dict[str, list[AddressAssignment]], devices: dict[str, Device]) -> list[str]:
    routers = [device.name for device in plan.devices if device.kind == "router"]
    adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for link in plan.links:
        if devices.get(link.a_device, Device("x", "pc", "x")).kind == "router" and devices.get(link.b_device, Device("x", "pc", "x")).kind == "router":
            a_ip = _address_for(addresses, link.a_device, link.a_interface)
            b_ip = _address_for(addresses, link.b_device, link.b_interface)
            if a_ip and b_ip:
                adjacency[link.a_device].append((link.b_device, b_ip))
                adjacency[link.b_device].append((link.a_device, a_ip))

    connected = {assignment.network for assignment in addresses.get(device_name, [])}
    network_owner: dict[str, str] = {}
    for router in routers:
        for assignment in addresses.get(router, []):
            network_owner.setdefault(assignment.network, router)

    routes: list[str] = []
    for network, owner in sorted(network_owner.items()):
        if owner == device_name or network in connected:
            continue
        next_hop = _next_hop(device_name, owner, adjacency)
        if next_hop:
            net = ipaddress.ip_network(network)
            routes.append(f"ip route {net.network_address} {net.netmask} {next_hop}")
    return routes


def _next_hop(source: str, target: str, adjacency: dict[str, list[tuple[str, str]]]) -> str | None:
    queue = deque([(source, None)])
    visited = {source}
    while queue:
        current, first_hop = queue.popleft()
        for neighbor, neighbor_ip in adjacency.get(current, []):
            if neighbor in visited:
                continue
            hop = neighbor_ip if current == source else first_hop
            if neighbor == target:
                return hop
            visited.add(neighbor)
            queue.append((neighbor, hop))
    return None


def _addresses_by_device(addresses: list[AddressAssignment]) -> dict[str, list[AddressAssignment]]:
    result: dict[str, list[AddressAssignment]] = defaultdict(list)
    for assignment in addresses:
        result[assignment.device].append(assignment)
    return result


def _links_by_endpoint(links: list[Link]) -> dict[tuple[str, str], Link]:
    result: dict[tuple[str, str], Link] = {}
    for link in links:
        result[(link.a_device, link.a_interface)] = link
        result[(link.b_device, link.b_interface)] = link
    return result


def _peer(link: Link, device: str, interface: str) -> tuple[str, str]:
    if (link.a_device, link.a_interface) == (device, interface):
        return link.b_device, link.b_interface
    return link.a_device, link.a_interface


def _address_for(addresses: dict[str, list[AddressAssignment]], device: str, interface: str) -> str | None:
    assignment = next((item for item in addresses.get(device, []) if item.interface == interface), None)
    return assignment.address if assignment else None


def _wildcard(mask: str) -> str:
    try:
        return str(ipaddress.ip_address(int(ipaddress.ip_address("255.255.255.255")) ^ int(ipaddress.ip_address(mask))))
    except ValueError as exc:
        raise TopologyValidationError(f"Invalid subnet mask {mask!r}") from exc


def _router_id(name: str) -> str:
    digits = "".join(character for character in name if character.isdigit()) or "1"
    return f"0.0.0.{int(digits)}"
