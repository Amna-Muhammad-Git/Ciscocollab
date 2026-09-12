"""MCP entry point for the Packet Tracer helper."""

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("packet-tracer-helper")


@mcp.tool()
def design_topology(
    routers: int = 2,
    switches: int = 1,
    pcs: int = 2,
    routing_protocol: str = "ospf",
    base_network: str = "192.168.0.0/16",
) -> dict:
    """Design a basic lab topology and return a structured plan.

    This initial scaffold validates the request. Address planning and topology
    generation will be added next, while keeping this response schema stable.
    """
    if routers < 0 or switches < 0 or pcs < 0:
        raise ValueError("Device counts cannot be negative")
    if routers + switches + pcs == 0:
        raise ValueError("At least one device is required")
    allowed_protocols = {"none", "static", "ospf"}
    protocol = routing_protocol.lower().strip()
    if protocol not in allowed_protocols:
        raise ValueError(f"routing_protocol must be one of {sorted(allowed_protocols)}")

    return {
        "status": "scaffold",
        "request": {
            "routers": routers,
            "switches": switches,
            "pcs": pcs,
            "routing_protocol": protocol,
            "base_network": base_network,
        },
        "message": "Topology generation is the next implementation step.",
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
