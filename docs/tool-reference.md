# MCP tool reference

## `design_topology`

Simple use: ask for a number of routers, switches, and PCs.

Technical inputs:

```json
{
  "routers": 2,
  "switches": 1,
  "pcs": 2,
  "routing_protocol": "ospf",
  "base_network": "192.168.0.0/16"
}
```

The result contains a `plan` object with `devices`, `links`, `addresses`,
`vlans`, `routing_protocol`, and `notes`. Pass that `plan` to the other tools.

## `generate_configs`

Simple use: turn a plan into commands to paste into Packet Tracer.

Technical input:

```json
{
  "plan": { "devices": [], "links": [], "addresses": [] }
}
```

Router and switch entries contain a `config` string. PC entries contain
`host_settings` with an IP address, subnet mask, and default gateway.

## `render_diagram`

Simple use: create a picture-like representation of the plan.

Technical output: a Mermaid `flowchart LR` string with device nodes, link
labels, interfaces, and assigned IP addresses.

## `verify_config`

Simple use: check whether pasted configuration matches the plan.

Technical input:

```json
{
  "plan": { "devices": [], "links": [], "addresses": [] },
  "configs": {
    "R1": "hostname R1\n...",
    "SW1": "hostname SW1\n..."
  }
}
```

The result reports `ok` when all supplied device configurations pass, or
`issues_found` with per-device checks and readable issue messages.

## Error responses

Invalid tool input returns a structured response rather than a traceback:

```json
{
  "status": "error",
  "error": {
    "type": "invalid_request",
    "message": "routers must be a non-negative integer"
  }
}
```
