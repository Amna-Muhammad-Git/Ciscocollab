# Cisco Packet Tracer MCP Helper

This project is a local MCP server that helps students plan Cisco Packet
Tracer labs. You describe the lab in Claude Desktop, and the server returns:

- Devices and cable connections
- An IPv4 addressing plan
- Cisco IOS commands for routers and switches
- PC IP settings
- A Mermaid network diagram
- Feedback on pasted configurations

The server does not open Packet Tracer, drag devices, or edit `.pkt` files.
Packet Tracer's file format is private. You still build the lab and paste the
commands yourself; this project makes that work clearer and easier to check.

## Quick start

### 1. Requirements

- Linux
- Python 3.10 or newer
- Claude Desktop
- A free Claude account is sufficient for local MCP testing

Cisco Packet Tracer is optional while developing this server. Install it later
when you want to build and test the generated lab in the simulator.

### 2. Install this project

From the project directory:

```bash
cd /home/amna/Ciscocollab
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

### 3. Connect it to Claude Desktop

Open:

```text
~/.config/Claude/claude_desktop_config.json
```

Add the `mcpServers` entry shown in
[the Linux setup guide](docs/linux-claude-desktop.md). Preserve any existing
Claude settings, save the JSON, and restart Claude Desktop.

### 4. Try a prompt

```text
Design a small lab with 2 routers, 1 switch, and 2 PCs using OSPF.
Show the devices, connections, IP plan, Mermaid diagram, IOS configurations,
and PC IP settings.
```

## How the tools work

The normal workflow is:

```text
design_topology
      ↓
generate_configs + render_diagram
      ↓
Build the lab manually in Packet Tracer
      ↓
verify_config
```

Use `design_topology` first. Pass its returned `plan` to the other tools.
Detailed inputs and outputs are in [the tool reference](docs/tool-reference.md).

## Supported first version

Supported device models:

- Cisco 2911 routers
- Cisco 2960 switches
- Packet Tracer PCs (`PC-PT`)

Supported routing choices:

- No routing protocol (`none`)
- Static routing (`static`)
- Single-area OSPF (`ospf`)

The planner uses `/30` networks for direct router links and `/24` networks for
switch-connected LANs. The default address space is `192.168.0.0/16`, but it
can be changed with the `base_network` input.

## Run tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```

The test suite covers model validation, topology design, IP allocation, IOS
generation, diagrams, MCP discovery, configuration verification, and the full
end-to-end workflow.

## Manual Packet Tracer validation

After installing Packet Tracer, follow [the validation checklist](docs/packet-tracer-validation.md).
This is important because automated tests can verify our logic, but only the
simulator can confirm that a particular IOS command behaves as expected in the
chosen Packet Tracer device model.

## Current limitations

- The student must create the topology manually in Packet Tracer.
- VLAN port assignment is basic in this first version.
- The configuration checker focuses on important settings, not every IOS command.
- Advanced features such as BGP, NAT, ACLs, DHCP, and IPv6 are not implemented.
- Mermaid is returned as text; Claude or a Mermaid viewer renders it visually.

## Project structure

```text
src/packet_tracer_mcp/
  models.py       Shared topology data model and validation
  topology.py     Physical topology planner
  addressing.py   IPv4 subnet and host allocation
  configs.py      IOS and PC configuration renderer
  diagrams.py     Mermaid diagram renderer
  verify.py       Pasted configuration checker
  server.py       MCP entry point and tool registration
tests/            Automated tests
docs/             Setup, tool, and manual validation guides
```

## Optional packaging

The server currently runs directly from the virtual environment, which is the
simplest development setup. A Claude Desktop `.mcpb` extension can be added
later for one-click installation after the server behavior and Packet Tracer
commands have been validated manually.
