import unittest

from packet_tracer_mcp.backends.base import (
    BackendCapabilities,
    BackendError,
    BackendOperation,
    LabBackend,
)
from packet_tracer_mcp.backends.packet_tracer import PacketTracerBackend
from packet_tracer_mcp.backends.registry import BackendRegistry
from packet_tracer_mcp.models import TopologyPlan


class ExampleBackend(LabBackend):
    name = "example"
    capabilities = BackendCapabilities(frozenset({BackendOperation.GENERATE}))

    def generate(self, plan: TopologyPlan) -> dict:
        return {"status": "generated"}


class BackendTests(unittest.TestCase):
    def test_registry_registers_and_selects_backends(self) -> None:
        registry = BackendRegistry()
        registry.register(ExampleBackend())
        self.assertEqual(registry.names(), ("example",))
        self.assertIsInstance(registry.get("EXAMPLE"), ExampleBackend)

    def test_registry_rejects_duplicates_and_unknown_names(self) -> None:
        registry = BackendRegistry()
        registry.register(ExampleBackend())
        with self.assertRaises(BackendError):
            registry.register(ExampleBackend())
        with self.assertRaises(BackendError):
            registry.get("missing")

    def test_packet_tracer_backend_is_plan_only(self) -> None:
        backend = PacketTracerBackend()
        self.assertTrue(backend.capabilities.supports(BackendOperation.GENERATE))
        self.assertFalse(backend.capabilities.supports(BackendOperation.DEPLOY))
        with self.assertRaises(BackendError):
            backend.destroy("lab", confirmed=True)


if __name__ == "__main__":
    unittest.main()
