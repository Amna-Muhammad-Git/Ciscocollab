"""MCP entry point for the Packet Tracer helper."""

from mcp.server.fastmcp import FastMCP

from .addressing import allocate_addresses
from .configs import generate_configurations
from .models import TopologyPlan, TopologyValidationError
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
    except (TopologyValidationError, TypeError, AttributeError) as exc:
        return _error_response("invalid_request", str(exc))
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
    """Generate paste-ready IOS and Packet Tracer host settings."""
    try:
        if not isinstance(plan, dict):
            raise ValueError("plan must be a JSON object")
        plan_data = plan.get("plan", plan)
        return generate_configurations(TopologyPlan.from_dict(plan_data))
    except (TopologyValidationError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return _error_response("invalid_plan", str(exc))


def _error_response(error_type: str, message: str) -> dict:
    """Return a Claude-readable tool error without exposing a traceback."""
    return {
        "status": "error",
        "error": {
            "type": error_type,
            "message": message,
        },
    }


def main() -> None:
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
