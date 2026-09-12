import unittest

from packet_tracer_mcp.models import (
    AddressAssignment,
    Device,
    Link,
    TopologyPlan,
    TopologyValidationError,
    Vlan,
)


class TopologyPlanTests(unittest.TestCase):
    def make_plan(self) -> TopologyPlan:
        return TopologyPlan(
            devices=[
                Device("R1", "router", "2911", ["GigabitEthernet0/0"]),
                Device("SW1", "switch", "2960", ["GigabitEthernet0/1"]),
            ],
            links=[Link("R1", "GigabitEthernet0/0", "SW1", "GigabitEthernet0/1")],
            addresses=[AddressAssignment("R1", "GigabitEthernet0/0", "192.168.1.0/24", "192.168.1.1", "255.255.255.0")],
            vlans=[Vlan(10, "STUDENTS")],
            routing_protocol="ospf",
        )

    def test_round_trip_to_and_from_dict(self) -> None:
        plan = self.make_plan()
        self.assertEqual(TopologyPlan.from_dict(plan.to_dict()).to_dict(), plan.to_dict())

    def test_rejects_unknown_link_interface(self) -> None:
        with self.assertRaisesRegex(TopologyValidationError, "unknown interface"):
            TopologyPlan(
                devices=[Device("R1", "router", "2911", ["GigabitEthernet0/0"])],
                links=[Link("R1", "GigabitEthernet0/1", "R1", "GigabitEthernet0/0")],
            )

    def test_rejects_duplicate_device_names(self) -> None:
        with self.assertRaisesRegex(TopologyValidationError, "Duplicate"):
            TopologyPlan(devices=[Device("R1", "router", "2911"), Device("R1", "router", "2911")])

    def test_rejects_invalid_protocol(self) -> None:
        with self.assertRaisesRegex(TopologyValidationError, "Unsupported routing"):
            TopologyPlan(routing_protocol="bgp")


if __name__ == "__main__":
    unittest.main()
