"""MCP entry point for the Packet Tracer helper."""

from mcp.server.fastmcp import FastMCP

from .addressing import allocate_addresses
from .automation import AutomationProfile, run_smoke_test
from .configs import generate_configurations
from .diagrams import render_mermaid
from .models import TopologyPlan, TopologyValidationError
from .topology import TopologyRequest, build_topology
from .verify import verify_configurations

mcp = FastMCP(
    "packet-tracer-helper",
    instructions=(
        "Use design_topology first. Pass its returned plan to generate_configs "
        "and render_diagram. After the student pastes configurations, pass the "
        "same plan and a device-to-text mapping to verify_config."
    ),
)


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


@mcp.tool()
def render_diagram(plan: dict) -> dict:
    """Render a topology plan as a Mermaid diagram."""
    try:
        if not isinstance(plan, dict):
            raise ValueError("plan must be a JSON object")
        plan_data = plan.get("plan", plan)
        return render_mermaid(TopologyPlan.from_dict(plan_data))
    except (TopologyValidationError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return _error_response("invalid_plan", str(exc))


@mcp.tool()
def verify_config(plan: dict, configs: dict[str, str]) -> dict:
    """Check pasted Cisco IOS configuration against a topology plan."""
    try:
        if not isinstance(plan, dict):
            raise ValueError("plan must be a JSON object")
        plan_data = plan.get("plan", plan)
        return verify_configurations(TopologyPlan.from_dict(plan_data), configs)
    except (TopologyValidationError, ValueError, KeyError, TypeError, AttributeError) as exc:
        return _error_response("invalid_input", str(exc))


@mcp.tool()
def packet_tracer_smoke_test(
    execute: bool = False,
    confirm: bool = False,
    coordinates: dict | None = None,
) -> dict:
    """Plan or explicitly execute a one-router Packet Tracer GUI smoke test."""
    try:
        values = coordinates or {}
        profile = AutomationProfile(
            router_palette=tuple(values.get("router_palette", AutomationProfile.router_palette)),
            canvas=tuple(values.get("canvas", AutomationProfile.canvas)),
            cli_tab=tuple(values.get("cli_tab", AutomationProfile.cli_tab)),
            cli_input=tuple(values.get("cli_input", AutomationProfile.cli_input)),
        )
        for name, point in vars(profile).items():
            if len(point) != 2 or not all(isinstance(value, int) and value >= 0 for value in point):
                raise ValueError(f"{name} must contain two non-negative integer coordinates")
        return run_smoke_test(profile, execute=execute, confirm=confirm)
    except (ValueError, TypeError) as exc:
        return _error_response("invalid_automation_request", str(exc))


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
