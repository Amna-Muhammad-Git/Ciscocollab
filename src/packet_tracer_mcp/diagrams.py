"""Mermaid diagram rendering for Packet Tracer topology plans."""

from __future__ import annotations

from .models import AddressAssignment, Link, TopologyPlan


def render_mermaid(plan: TopologyPlan) -> dict:
    """Render a deterministic Mermaid flowchart from a validated topology."""
    addresses = {
        (assignment.device, assignment.interface): assignment
        for assignment in plan.addresses
    }
    lines = ["flowchart LR"]
    for device in plan.devices:
        kind_label = {"pc": "PC"}.get(device.kind, device.kind.title())
        label = f"{device.name}<br/>{kind_label} ({device.model})"
        lines.append(f'    {device.name}["{_escape(label)}"]')

    for link in plan.links:
        a_label = _endpoint_label(link.a_device, link.a_interface, addresses)
        b_label = _endpoint_label(link.b_device, link.b_interface, addresses)
        edge_label = f"{a_label} ↔ {b_label}"
        lines.append(
            f'    {link.a_device} ---|"{_escape(edge_label)}"| {link.b_device}'
        )

    lines.extend(
        [
            "    classDef router fill:#dbeafe,stroke:#2563eb,stroke-width:2px",
            "    classDef switch fill:#dcfce7,stroke:#16a34a,stroke-width:2px",
            "    classDef pc fill:#fef3c7,stroke:#d97706,stroke-width:2px",
        ]
    )
    for device in plan.devices:
        style = device.kind if device.kind in {"router", "switch", "pc"} else "pc"
        lines.append(f"    class {device.name} {style}")

    return {
        "status": "ok",
        "format": "mermaid",
        "diagram": "\n".join(lines),
        "legend": {
            "router": "Blue",
            "switch": "Green",
            "pc": "Yellow",
        },
    }


def _endpoint_label(
    device: str,
    interface: str,
    addresses: dict[tuple[str, str], AddressAssignment],
) -> str:
    assignment = addresses.get((device, interface))
    if assignment is None:
        return interface
    return f"{interface} {assignment.address}/{assignment.network.split('/')[-1]}"


def _escape(value: str) -> str:
    return value.replace('"', "&quot;")
