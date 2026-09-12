import unittest

from packet_tracer_mcp.addressing import allocate_addresses
from packet_tracer_mcp.configs import generate_configurations
from packet_tracer_mcp.models import TopologyPlan
from packet_tracer_mcp.topology import TopologyRequest, build_topology


class ConfigurationTests(unittest.TestCase):
    def make_plan(self, protocol: str = "ospf") -> TopologyPlan:
        plan = build_topology(TopologyRequest(2, 1, 2, protocol, "192.168.0.0/16"))
        plan.addresses = allocate_addresses(plan, "192.168.0.0/16").addresses
        plan.validate()
        return plan

    def test_generates_router_switch_and_pc_output(self) -> None:
        output = generate_configurations(self.make_plan())
        router = next(item for item in output["devices"] if item["name"] == "R1")
        switch = next(item for item in output["devices"] if item["name"] == "SW1")
        pc = next(item for item in output["devices"] if item["name"] == "PC1")
        self.assertIn("hostname R1", router["config"])
        self.assertIn("router ospf 1", router["config"])
        self.assertIn("network 192.168.1.0 0.0.0.255 area 0", router["config"])
        self.assertIn("switchport mode access", switch["config"])
        self.assertEqual(pc["host_settings"]["ip_address"], "192.168.1.3")

    def test_generates_static_routes(self) -> None:
        output = generate_configurations(self.make_plan("static"))
        router = next(item for item in output["devices"] if item["name"] == "R1")
        self.assertIn("hostname R1", router["config"])

    def test_empty_addresses_produce_shutdown_interfaces(self) -> None:
        plan = build_topology(TopologyRequest(1, 1, 1))
        output = generate_configurations(plan)
        router = next(item for item in output["devices"] if item["name"] == "R1")
        self.assertIn(" shutdown", router["config"])


if __name__ == "__main__":
    unittest.main()
