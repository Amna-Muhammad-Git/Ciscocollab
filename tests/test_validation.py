import unittest

from packet_tracer_mcp.models import AddressAssignment, Device, TopologyPlan, TopologyValidationError
from packet_tracer_mcp.server import design_topology, generate_configs


class ValidationTests(unittest.TestCase):
    def test_rejects_invalid_ip_assignment(self) -> None:
        with self.assertRaises(TopologyValidationError):
            AddressAssignment("R1", "GigabitEthernet0/0", "192.168.1.0/24", "192.168.2.1", "255.255.255.0")

    def test_rejects_duplicate_ip_addresses(self) -> None:
        with self.assertRaises(TopologyValidationError):
            TopologyPlan(
                devices=[
                    Device("R1", "router", "2911", ["GigabitEthernet0/0"]),
                    Device("R2", "router", "2911", ["GigabitEthernet0/0"]),
                ],
                addresses=[
                    AddressAssignment("R1", "GigabitEthernet0/0", "192.168.1.0/24", "192.168.1.1", "255.255.255.0"),
                    AddressAssignment("R2", "GigabitEthernet0/0", "192.168.1.0/24", "192.168.1.1", "255.255.255.0"),
                ],
            )

    def test_mcp_tools_return_structured_errors(self) -> None:
        design_result = design_topology(routers=-1)
        config_result = generate_configs({"plan": {"devices": "invalid"}})
        self.assertEqual(design_result["status"], "error")
        self.assertEqual(design_result["error"]["type"], "invalid_request")
        self.assertEqual(config_result["status"], "error")
        self.assertIn("devices must be a list", config_result["error"]["message"])


if __name__ == "__main__":
    unittest.main()
