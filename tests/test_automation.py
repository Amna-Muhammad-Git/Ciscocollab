import unittest

from packet_tracer_mcp.automation import AutomationProfile, run_smoke_test, smoke_test_steps
from packet_tracer_mcp.server import packet_tracer_smoke_test


class AutomationTests(unittest.TestCase):
    def test_dry_run_never_controls_desktop(self) -> None:
        result = run_smoke_test()
        self.assertEqual(result["status"], "dry_run")
        self.assertEqual(result["steps"][0]["action"], "launch")
        self.assertEqual(result["steps"][-2]["text"], "enable")

    def test_execution_requires_two_guards(self) -> None:
        self.assertEqual(run_smoke_test(execute=True)["status"], "blocked")
        self.assertEqual(run_smoke_test(execute=True, confirm=True)["status"], "blocked")

    def test_custom_coordinates_are_returned(self) -> None:
        profile = AutomationProfile(canvas=(10, 20))
        steps = smoke_test_steps(profile)
        canvas_step = next(step for step in steps if step.get("target") == "canvas")
        self.assertEqual(canvas_step["coordinates"], (10, 20))

    def test_mcp_tool_defaults_to_dry_run(self) -> None:
        result = packet_tracer_smoke_test()
        self.assertEqual(result["status"], "dry_run")

if __name__ == "__main__":
    unittest.main()
