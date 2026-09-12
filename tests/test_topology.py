import unittest

from packet_tracer_mcp.models import TopologyValidationError
from packet_tracer_mcp.topology import TopologyRequest, build_topology


class TopologyBuilderTests(unittest.TestCase):
    def test_builds_router_switch_pc_lab(self) -> None:
        plan = build_topology(TopologyRequest(routers=2, switches=1, pcs=2))
        self.assertEqual([device.name for device in plan.devices], ["R1", "R2", "SW1", "PC1", "PC2"])
        self.assertEqual(len(plan.links), 5)
        self.assertEqual(plan.links[0].a_device, "R1")
        self.assertEqual(plan.links[0].b_device, "R2")
        self.assertIn("GigabitEthernet0/0", plan.devices[0].interfaces)
        self.assertEqual(plan.devices[-1].interfaces, ["FastEthernet0"])
        self.assertEqual(plan.addresses, [])

    def test_builds_switch_and_pc_lab_without_routers(self) -> None:
        plan = build_topology(TopologyRequest(routers=0, switches=1, pcs=2))
        self.assertEqual(len(plan.links), 2)
        self.assertTrue(all(link.b_device == "SW1" for link in plan.links))

    def test_builds_router_and_pc_lab_without_switches(self) -> None:
        plan = build_topology(TopologyRequest(routers=1, switches=0, pcs=2))
        self.assertEqual(len(plan.links), 2)
        self.assertTrue(all(link.b_device == "R1" for link in plan.links))

    def test_rejects_invalid_requests(self) -> None:
        with self.assertRaises(TopologyValidationError):
            TopologyRequest(routers=-1)
        with self.assertRaises(TopologyValidationError):
            TopologyRequest(routers=0, switches=0, pcs=0)
        with self.assertRaises(TopologyValidationError):
            TopologyRequest(routing_protocol="bgp")

    def test_is_deterministic(self) -> None:
        first = build_topology(TopologyRequest()).to_dict()
        second = build_topology(TopologyRequest()).to_dict()
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
