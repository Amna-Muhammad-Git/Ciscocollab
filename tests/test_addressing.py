import unittest

from packet_tracer_mcp.addressing import allocate_addresses
from packet_tracer_mcp.models import TopologyValidationError
from packet_tracer_mcp.topology import TopologyRequest, build_topology


class AddressingTests(unittest.TestCase):
    def test_assigns_lan_and_point_to_point_subnets(self) -> None:
        plan = build_topology(TopologyRequest(routers=2, switches=1, pcs=2))
        result = allocate_addresses(plan, "192.168.0.0/16")
        self.assertEqual(result.networks, ["192.168.0.0/30", "192.168.1.0/24"])
        self.assertEqual(len(result.addresses), 6)
        self.assertEqual(result.addresses[0].address, "192.168.0.1")
        self.assertEqual(result.addresses[-1].gateway, "192.168.1.1")
        self.assertEqual(len({assignment.network for assignment in result.addresses}), 2)

    def test_switch_ports_do_not_get_ip_addresses(self) -> None:
        plan = build_topology(TopologyRequest(routers=1, switches=1, pcs=1))
        result = allocate_addresses(plan, "10.0.0.0/16")
        self.assertTrue(all(assignment.device != "SW1" for assignment in result.addresses))

    def test_rejects_invalid_or_too_small_base_network(self) -> None:
        plan = build_topology(TopologyRequest(routers=1, switches=1, pcs=1))
        with self.assertRaises(TopologyValidationError):
            allocate_addresses(plan, "not-a-network")
        with self.assertRaises(TopologyValidationError):
            allocate_addresses(plan, "192.168.1.0/30")

    def test_allocation_is_deterministic(self) -> None:
        plan = build_topology(TopologyRequest())
        first = allocate_addresses(plan, "172.16.0.0/16")
        second = allocate_addresses(plan, "172.16.0.0/16")
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
