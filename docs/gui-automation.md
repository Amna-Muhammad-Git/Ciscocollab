# Packet Tracer GUI automation prototype

This is an experimental bridge for reducing clicks in Packet Tracer. It is
not a Packet Tracer API. It uses screen coordinates, so coordinates may need to
be calibrated for your display, window size, desktop scaling, and Packet Tracer
version.

## Safe dry run

Ask Claude:

```text
Run the Packet Tracer smoke test in dry-run mode and show me every action.
```

The default behavior only returns the planned actions. It does not open an
application or move the mouse.

## Optional setup

From the project directory:

```bash
.venv/bin/python -m pip install -e '.[gui]'
```

GUI automation generally works best under an X11 desktop session. Wayland,
display scaling, and window focus can prevent coordinate-based automation from
working reliably.

## MCP safety boundary

The exposed MCP tool is permanently dry-run only. Claude can never use it to
launch Packet Tracer, move the mouse, or type into applications. It only
returns a list of proposed actions and coordinates.

The lower-level Python helper contains an experimental execution path for
future local development, but it is not exposed as an MCP tool. Any future
execution feature must be a separately launched local program with an
interactive confirmation owned by the user.

No desktop permissions, application control, or keyboard/mouse access are
requested by the MCP server.

## Coordinate calibration

The initial coordinates are only placeholders. Pass custom coordinates when
calling the tool:

```json
{
  "execute": false,
  "coordinates": {
    "router_palette": [105, 255],
    "canvas": [650, 400],
    "cli_tab": [760, 730],
    "cli_input": [700, 650]
  }
}
```

The prototype currently describes placing one router and typing `enable`; it
does not execute those actions or build a complete lab.
