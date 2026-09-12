import unittest

from packet_tracer_mcp.addressing import allocate_addresses
from packet_tracer_mcp.configs import generate_configurations
from packet_tracer_mcp.models import TopologyPlan
from packet_tracer_mcp.server import verify_config
from packet_tracer_mcp.verify import verify_configurations
from packet_tracer_mcp.topology import TopologyRequest, build_topology


class VerifyTests(unittest.TestCase):
    def make_plan(self) -> TopologyPlan:
        plan = build_topology(TopologyRequest(2, 1, 2, "ospf", "192.168.0.0/16"))
        plan.addresses = allocate_addresses(plan, "192.168.0.0/16").addresses
        plan.validate()
        return plan

    def test_accepts_generated_router_and_switch_configs(self) -> None:
        plan = self.make_plan()
        generated = generate_configurations(plan)
        configs = {item["name"]: item["config"] for item in generated["devices"] if "config" in item}
        result = verify_configurations(plan, configs)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["summary"]["failed"], 0)

    def test_reports_wrong_ip_and_missing_shutdown(self) -> None:
        plan = self.make_plan()
        config = """hostname R1
interface GigabitEthernet0/0
 ip address 10.0.0.1 255.255.255.252
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
 no shutdown
router ospf 1
 network 192.168.0.0 0.0.0.3 area 0
 network 192.168.1.0 0.0.0.255 area 0
end
"""
        result = verify_configurations(plan, {"R1": config})
        self.assertEqual(result["status"], "issues_found")
        self.assertTrue(any("Expected `ip address 192.168.0.1" in issue for issue in result["results"][0]["issues"]))
        self.assertTrue(any("GigabitEthernet0/0 state" in issue for issue in result["results"][0]["issues"]))

    def test_mcp_tool_returns_error_for_bad_input(self) -> None:
        result = verify_config({}, [])
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["error"]["type"], "invalid_input")


if __name__ == "__main__":
    unittest.main()
