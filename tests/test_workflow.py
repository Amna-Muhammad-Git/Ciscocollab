import unittest

from packet_tracer_mcp.addressing import allocate_addresses
from packet_tracer_mcp.configs import generate_configurations
from packet_tracer_mcp.diagrams import render_mermaid
from packet_tracer_mcp.models import TopologyPlan
from packet_tracer_mcp.topology import TopologyRequest, build_topology
from packet_tracer_mcp.verify import verify_configurations


class EndToEndWorkflowTests(unittest.TestCase):
    def build_plan(self) -> TopologyPlan:
        plan = build_topology(TopologyRequest(2, 1, 2, "ospf", "10.10.0.0/16"))
        plan.addresses = allocate_addresses(plan, "10.10.0.0/16").addresses
        plan.validate()
        return plan

    def test_complete_student_workflow(self) -> None:
        plan = self.build_plan()
        configurations = generate_configurations(plan)
        configs = {
            item["name"]: item["config"]
            for item in configurations["devices"]
            if "config" in item
        }
        diagram = render_mermaid(plan)
        verification = verify_configurations(plan, configs)

        self.assertEqual(len(plan.devices), 5)
        self.assertEqual(len(plan.links), 5)
        self.assertEqual(configurations["status"], "ok")
        self.assertTrue(diagram["diagram"].startswith("flowchart LR"))
        self.assertEqual(verification["status"], "ok")

    def test_workflow_detects_a_student_typo(self) -> None:
        plan = self.build_plan()
        configurations = generate_configurations(plan)
        configs = {
            item["name"]: item["config"]
            for item in configurations["devices"]
            if "config" in item
        }
        configs["R1"] = configs["R1"].replace("no shutdown", "shutdown", 1)
        verification = verify_configurations(plan, configs)

        self.assertEqual(verification["status"], "issues_found")
        self.assertGreater(verification["summary"]["failed"], 0)

    def test_workflow_supports_static_routing_request(self) -> None:
        plan = build_topology(TopologyRequest(2, 1, 2, "static", "172.16.0.0/16"))
        plan.addresses = allocate_addresses(plan, "172.16.0.0/16").addresses
        plan.validate()
        output = generate_configurations(plan)
        router = next(item for item in output["devices"] if item["name"] == "R1")
        self.assertIn("hostname R1", router["config"])
        self.assertNotIn("router ospf", router["config"])


if __name__ == "__main__":
    unittest.main()
