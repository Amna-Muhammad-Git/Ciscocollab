import unittest

from packet_tracer_mcp.addressing import allocate_addresses
from packet_tracer_mcp.backends.containerlab import (
    ContainerlabBackend,
    ContainerlabProfile,
    generate_containerlab_yaml,
)
from packet_tracer_mcp.models import TopologyPlan
from packet_tracer_mcp.topology import TopologyRequest, build_topology


class ContainerlabTests(unittest.TestCase):
    def make_plan(self) -> TopologyPlan:
        plan = build_topology(TopologyRequest(2, 1, 2, "ospf", "192.168.0.0/16"))
        plan.addresses = allocate_addresses(plan, "192.168.0.0/16").addresses
        plan.validate()
        return plan

    def test_generates_deterministic_yaml_and_interface_mapping(self) -> None:
        result = generate_containerlab_yaml(self.make_plan())
        self.assertIn("name: 'packet-tracer-lab'", result["yaml"])
        self.assertIn("r1:", result["yaml"])
        self.assertIn("image: 'frrouting/frr:latest'", result["yaml"])
        self.assertIn("- endpoints: ['r1:eth1', 'r2:eth1']", result["yaml"])
        self.assertEqual(result["node_interfaces"]["R1"]["GigabitEthernet0/0"], "eth1")
        self.assertEqual(result, generate_containerlab_yaml(self.make_plan()))

    def test_custom_profile_changes_images(self) -> None:
        profile = ContainerlabProfile(router_image="example/router:1")
        result = generate_containerlab_yaml(self.make_plan(), profile)
        self.assertIn("image: 'example/router:1'", result["yaml"])

    def test_free_frr_profile_is_explicit_and_described(self) -> None:
        profile = ContainerlabProfile.free_frr()
        self.assertEqual(profile.PROFILE_NAME, "frr-free")
        self.assertEqual(profile.describe()["router_image"], "frrouting/frr:latest")

    def test_rejects_invalid_image_values(self) -> None:
        with self.assertRaises(ValueError):
            ContainerlabProfile(router_image="")
        with self.assertRaises(ValueError):
            ContainerlabProfile(router_image="frrouting/frr:\nlatest")

    def test_backend_returns_yaml_artifact(self) -> None:
        result = ContainerlabBackend().generate(self.make_plan())
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["format"], "containerlab-yaml")
        self.assertTrue(result["filename"].endswith(".clab.yml"))
        self.assertTrue(result["warnings"])


if __name__ == "__main__":
    unittest.main()
