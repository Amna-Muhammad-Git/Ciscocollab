"""MCP entry point for the Packet Tracer helper."""

from mcp.server.fastmcp import FastMCP

from .addressing import allocate_addresses
from .models import TopologyValidationError
from .topology import TopologyRequest, build_topology

mcp = FastMCP("packet-tracer-helper")


@mcp.tool()
def design_topology(
    routers: int = 2,
    switches: int = 1,
    pcs: int = 2,
    routing_protocol: str = "ospf",
    base_network: str = "192.168.0.0/16",
) -> dict:
    """Design a deterministic physical lab and return its canonical plan."""
    try:
        request = TopologyRequest(routers, switches, pcs, routing_protocol, base_network)
        plan = build_topology(request)
        addressing = allocate_addresses(plan, request.base_network)
        plan.addresses = addressing.addresses
        plan.validate()
    except (TopologyValidationError, AttributeError) as exc:
        raise ValueError(str(exc)) from exc
    return {
        "status": "ok",
        "plan": plan.to_dict(),
        "summary": {
            "devices": len(plan.devices),
            "links": len(plan.links),
            "routers": routers,
            "switches": switches,
            "pcs": pcs,
            "networks": addressing.networks,
        },
    }


@mcp.tool()
def generate_configs(plan: dict) -> dict:
    """Generate IOS configuration from a topology plan.

    The full renderer will consume the canonical plan returned by
    design_topology. This placeholder makes the intended tool contract clear.
    """
    if not isinstance(plan, dict):
        raise ValueError("plan must be a JSON object")
    return {
        "status": "scaffold",
        "message": "Configuration generation is not implemented yet.",
        "input_keys": sorted(plan),
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
