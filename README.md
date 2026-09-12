# Packet Tracer MCP

A local MCP server that helps students design Cisco Packet Tracer labs and generate IOS configuration. It does not modify `.pkt` files or control Packet Tracer directly.

## Development setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
packet-tracer-mcp
```

The server uses MCP `stdio` transport and is intended for Claude Desktop on Linux.
