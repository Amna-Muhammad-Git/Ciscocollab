import unittest

from packet_tracer_mcp.addressing import allocate_addresses
from packet_tracer_mcp.diagrams import render_mermaid
from packet_tracer_mcp.models import TopologyPlan
from packet_tracer_mcp.server import render_diagram
from packet_tracer_mcp.topology import TopologyRequest, build_topology


class DiagramTests(unittest.TestCase):
    def make_plan(self) -> TopologyPlan:
        plan = build_topology(TopologyRequest(2, 1, 2, "ospf", "192.168.0.0/16"))
        plan.addresses = allocate_addresses(plan, "192.168.0.0/16").addresses
        plan.validate()
        return plan

    def test_renders_devices_links_and_addresses(self) -> None:
        output = render_mermaid(self.make_plan())
        diagram = output["diagram"]
        self.assertEqual(output["format"], "mermaid")
        self.assertIn("flowchart LR", diagram)
        self.assertIn('R1["R1<br/>Router (2911)"]', diagram)
        self.assertIn('SW1["SW1<br/>Switch (2960)"]', diagram)
        self.assertIn('PC1["PC1<br/>PC (PC-PT)"]', diagram)
        self.assertIn("GigabitEthernet0/0 192.168.0.1/30", diagram)
        self.assertIn("PC1 ---|", diagram)

    def test_rendering_is_deterministic(self) -> None:
        plan = self.make_plan()
        self.assertEqual(render_mermaid(plan), render_mermaid(plan))

    def test_mcp_tool_accepts_design_response(self) -> None:
        plan = self.make_plan().to_dict()
        output = render_diagram({"plan": plan})
        self.assertEqual(output["status"], "ok")
        self.assertIn("flowchart LR", output["diagram"])


if __name__ == "__main__":
    unittest.main()
