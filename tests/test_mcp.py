import asyncio
import json
import unittest

from packet_tracer_mcp.server import mcp


class McpIntegrationTests(unittest.TestCase):
    def test_all_tools_are_discoverable_with_schemas(self) -> None:
        tools = asyncio.run(mcp.list_tools())
        self.assertEqual(
            {tool.name for tool in tools},
            {
                "design_topology",
                "generate_configs",
                "render_diagram",
                "verify_config",
                "packet_tracer_smoke_test",
            },
        )
        by_name = {tool.name: tool for tool in tools}
        self.assertIn("plan", by_name["generate_configs"].inputSchema["required"])
        self.assertIn("configs", by_name["verify_config"].inputSchema["required"])
        self.assertNotIn("execute", by_name["packet_tracer_smoke_test"].inputSchema["properties"])
        self.assertNotIn("confirm", by_name["packet_tracer_smoke_test"].inputSchema["properties"])

    def test_mcp_call_supports_design_to_config_chain(self) -> None:
        content = asyncio.run(mcp.call_tool("design_topology", {"routers": 1, "switches": 1, "pcs": 1}))
        response = json.loads(content[0].text)
        plan = response["plan"]
        config_content = asyncio.run(mcp.call_tool("generate_configs", {"plan": plan}))
        config_response = json.loads(config_content[0].text)
        self.assertEqual(config_response["status"], "ok")
        self.assertEqual({item["name"] for item in config_response["devices"]}, {"R1", "SW1", "PC1"})


if __name__ == "__main__":
    unittest.main()
