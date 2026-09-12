"""Safe first prototype for Packet Tracer desktop automation.

The prototype uses screen coordinates because Packet Tracer does not expose a
supported automation API. It is dry-run by default and requires explicit
confirmation before it launches an application or sends keyboard/mouse input.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class AutomationProfile:
    """Coordinates for one Packet Tracer UI layout."""

    router_palette: tuple[int, int] = (105, 255)
    canvas: tuple[int, int] = (650, 400)
    cli_tab: tuple[int, int] = (760, 730)
    cli_input: tuple[int, int] = (700, 650)


def smoke_test_steps(profile: AutomationProfile) -> list[dict]:
    """Return the human-readable actions the prototype would perform."""
    return [
        {"action": "launch", "command": "packettracer"},
        {"action": "wait", "seconds": 8},
        {"action": "click", "target": "router_palette", "coordinates": profile.router_palette},
        {"action": "click", "target": "canvas", "coordinates": profile.canvas},
        {"action": "click", "target": "cli_tab", "coordinates": profile.cli_tab},
        {"action": "click", "target": "cli_input", "coordinates": profile.cli_input},
        {"action": "type", "text": "enable"},
        {"action": "press", "key": "enter"},
    ]


def run_smoke_test(
    profile: AutomationProfile | None = None,
    *,
    execute: bool = False,
    confirm: bool = False,
) -> dict:
    """Plan or execute the one-router GUI smoke test.

    `execute=True` and `confirm=True` are both required for desktop control.
    Set `PACKET_TRACER_AUTOMATION_ENABLED=1` as a third explicit guard.
    """
    profile = profile or AutomationProfile()
    steps = smoke_test_steps(profile)
    if not execute:
        return {
            "status": "dry_run",
            "message": "No application was opened and no input was sent.",
            "steps": steps,
            "profile": asdict(profile),
        }
    if not confirm:
        return {"status": "blocked", "message": "Set confirm=true to authorize desktop input.", "steps": steps}
    if os.environ.get("PACKET_TRACER_AUTOMATION_ENABLED") != "1":
        return {
            "status": "blocked",
            "message": "Set PACKET_TRACER_AUTOMATION_ENABLED=1 to enable desktop input.",
            "steps": steps,
        }
    if not shutil.which("packettracer"):
        return {"status": "error", "message": "The packettracer command was not found.", "steps": steps}
    try:
        import pyautogui
    except ImportError:
        return {
            "status": "error",
            "message": "pyautogui is required. Install it with: .venv/bin/python -m pip install pyautogui",
            "steps": steps,
        }
    if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
        return {"status": "error", "message": "No graphical display was detected.", "steps": steps}

    pyautogui.FAILSAFE = True
    pyautogui.PAUSE = 0.25
    process = subprocess.Popen(["packettracer"])
    time.sleep(8)
    pyautogui.click(*profile.router_palette)
    pyautogui.click(*profile.canvas)
    pyautogui.click(*profile.cli_tab)
    pyautogui.click(*profile.cli_input)
    pyautogui.write("enable")
    pyautogui.press("enter")
    return {
        "status": "executed",
        "message": "One-router GUI smoke test actions were sent to Packet Tracer.",
        "pid": process.pid,
        "steps": steps,
        "safety": "Move the mouse to the top-left corner to trigger pyautogui failsafe.",
    }
