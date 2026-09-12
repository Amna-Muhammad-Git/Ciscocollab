# Claude Desktop on Linux

Claude Desktop is installed separately from this project. The MCP server runs
locally through the Python executable in this repository.

Configuration file:

```text
~/.config/Claude/claude_desktop_config.json
```

Add this top-level property while preserving any existing properties:

```json
"mcpServers": {
  "packet-tracer-helper": {
    "command": "/home/amna/Ciscocollab/.venv/bin/packet-tracer-mcp"
  }
}
```

For example, the file can contain:

```json
{
  "preferences": {},
  "mcpServers": {
    "packet-tracer-helper": {
      "command": "/home/amna/Ciscocollab/.venv/bin/packet-tracer-mcp"
    }
  }
}
```

After saving the file, fully restart Claude Desktop. Open the tool/connector
panel and confirm these tools are visible:

- `design_topology`
- `generate_configs`
- `render_diagram`
- `verify_config`

Test prompt:

```text
Design a small lab with 2 routers, 1 switch, and 2 PCs using OSPF. Show me
the topology, IP addressing plan, diagram, and configurations.
```

The server must be started by Claude Desktop; do not run it in a terminal at
the same time while testing the desktop connection.
