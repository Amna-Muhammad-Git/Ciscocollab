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

## Explicit execution safeguards

The tool requires all three conditions before sending input:

1. `execute=true`
2. `confirm=true`
3. The environment variable below:

   ```bash
   export PACKET_TRACER_AUTOMATION_ENABLED=1
   ```

The emergency stop is pyautogui's failsafe: move the mouse to the top-left
corner of the screen.

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

First validate the dry run. Only execute it after the Packet Tracer window is
open, focused, and the coordinates have been checked. The prototype currently
places one router and types `enable`; it does not yet build a complete lab.
