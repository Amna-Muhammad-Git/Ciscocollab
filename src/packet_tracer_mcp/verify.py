"""Lightweight verification of pasted Cisco IOS configurations."""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass

from .models import AddressAssignment, Device, TopologyPlan


@dataclass
class ParsedConfig:
    hostname: str | None
    interfaces: dict[str, list[str]]
    global_commands: list[str]


def verify_configurations(plan: TopologyPlan, configs: dict[str, str]) -> dict:
    """Compare pasted configurations with the expected topology plan."""
    if not isinstance(configs, dict):
        raise ValueError("configs must be an object mapping device names to config text")
    expected = {device.name: device for device in plan.devices}
    results: list[dict] = []
    for name, text in configs.items():
        if name not in expected:
            results.append({"device": name, "status": "error", "issues": ["Device is not present in the topology plan"]})
            continue
        if not isinstance(text, str):
            results.append({"device": name, "status": "error", "issues": ["Configuration must be text"]})
            continue
        results.append(_verify_device(expected[name], plan, _parse_config(text)))

    for device in plan.devices:
        if device.kind != "pc" and device.name not in configs:
            results.append({"device": device.name, "status": "error", "issues": ["No configuration was provided"]})

    passed = sum(item["status"] == "ok" for item in results)
    failed = len(results) - passed
    return {
        "status": "ok" if failed == 0 else "issues_found",
        "summary": {"devices_checked": len(results), "passed": passed, "failed": failed},
        "results": results,
    }


def _verify_device(device: Device, plan: TopologyPlan, parsed: ParsedConfig) -> dict:
    checks: list[dict] = []
    issues: list[str] = []
    _check(checks, issues, parsed.hostname == device.name, "hostname", f"Expected hostname {device.name}")

    if device.kind == "router":
        expected_addresses = [item for item in plan.addresses if item.device == device.name]
        for assignment in expected_addresses:
            commands = parsed.interfaces.get(assignment.interface, [])
            expected_ip = f"ip address {assignment.address} {assignment.mask}"
            _check(checks, issues, expected_ip in commands, f"{assignment.interface} IP", f"Expected `{expected_ip}`")
            _check(checks, issues, "no shutdown" in commands, f"{assignment.interface} state", "Interface should contain `no shutdown`")
        if plan.routing_protocol == "ospf":
            ospf_networks = _ospf_network_commands(parsed.global_commands)
            for assignment in expected_addresses:
                expected = f"network {assignment.network.split('/')[0]} {_wildcard(assignment.mask)} area 0"
                _check(checks, issues, expected in ospf_networks, "OSPF", f"Expected `{expected}`")
    elif device.kind == "switch":
        for vlan in plan.vlans:
            _check(checks, issues, f"vlan {vlan.vlan_id}" in parsed.global_commands, f"VLAN {vlan.vlan_id}", "VLAN is missing")
        for interface in device.interfaces:
            if interface in parsed.interfaces:
                _check(checks, issues, "no shutdown" in parsed.interfaces[interface], f"{interface} state", "Interface should contain `no shutdown`")

    return {"device": device.name, "status": "ok" if not issues else "issues_found", "checks": checks, "issues": issues}


def _parse_config(text: str) -> ParsedConfig:
    hostname = None
    interfaces: dict[str, list[str]] = {}
    global_commands: list[str] = []
    current_interface: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("!"):
            continue
        hostname_match = re.match(r"hostname\s+(\S+)$", line, re.IGNORECASE)
        if hostname_match:
            hostname = hostname_match.group(1)
            continue
        interface_match = re.match(r"interface\s+(\S+)$", line, re.IGNORECASE)
        if interface_match:
            current_interface = interface_match.group(1)
            interfaces.setdefault(current_interface, [])
            continue
        if line.lower() in {"exit", "end"}:
            current_interface = None
            continue
        if current_interface:
            interfaces[current_interface].append(line.lower())
        else:
            global_commands.append(line.lower())
    return ParsedConfig(hostname, interfaces, global_commands)


def _ospf_network_commands(commands: list[str]) -> list[str]:
    in_ospf = False
    networks: list[str] = []
    for command in commands:
        if command.startswith("router ospf "):
            in_ospf = True
            continue
        if in_ospf and command.startswith("network "):
            networks.append(command)
    return networks


def _check(checks: list[dict], issues: list[str], passed: bool, name: str, failure: str) -> None:
    checks.append({"name": name, "passed": passed})
    if not passed:
        issues.append(f"{name}: {failure}")


def _wildcard(mask: str) -> str:
    return str(ipaddress.ip_address(int(ipaddress.ip_address("255.255.255.255")) ^ int(ipaddress.ip_address(mask))))
