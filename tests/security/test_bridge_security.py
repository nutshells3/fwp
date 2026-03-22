from __future__ import annotations

import unittest

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_hub import build_reference_hub
from fwp_mcp_bridge import MCPBridge


class BridgeSecurityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()
        self.hub = build_reference_hub()
        self.bridge = MCPBridge(self.hub, repo_root=self.root)
        self.hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}}})
        workspace = self.hub.handle_request({"jsonrpc": "2.0", "id": 2, "method": "workspace/open", "params": {"rootUri": (self.root / "examples" / "workspaces" / "demo").as_uri(), "backendId": "isabelle-local"}})
        self.workspace_id = workspace["result"]["workspaceId"]
        build = self.hub.handle_request({"jsonrpc": "2.0", "id": 3, "method": "build/run", "params": {"workspaceId": self.workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}}})
        self.artifact_id = build["result"]["artifacts"][0]["artifactId"]

    def test_allowlist_blocks_unknown_tool(self) -> None:
        with self.assertRaises(PermissionError):
            self.bridge.call_tool("document.open", {})

    def test_schema_invalid_tool_input_is_rejected(self) -> None:
        with self.assertRaises(PermissionError):
            self.bridge.call_tool("workspace.open", {"backendId": "isabelle-local"})

    def test_resource_uri_restrictions(self) -> None:
        with self.assertRaises(PermissionError):
            self.bridge.read_resource("file:///etc/passwd")
        with self.assertRaises(PermissionError):
            self.bridge.read_resource("fwp://artifact/../secrets")

    def test_descriptor_resource_is_redacted(self) -> None:
        descriptor = self.bridge.read_resource("fwp://descriptor/isabelle-local")
        self.assertEqual(descriptor["argv"], ["[redacted]"])

    def test_artifact_resource_is_sanitized(self) -> None:
        resource = self.bridge.read_resource(f"fwp://artifact/{self.workspace_id}/{self.artifact_id}")
        self.assertIn("content", resource)

    def test_oversized_raw_payload_is_redacted(self) -> None:
        sanitized = self.bridge.policy.sanitize_result({"rawPayload": {"blob": "x" * 10_000}})
        self.assertEqual(sanitized["rawPayload"]["redacted"], True)

    def test_run_governance_tools_delegate_to_hub(self) -> None:
        started = self.bridge.call_tool(
            "backend.run.start",
            {
                "workspaceId": self.workspace_id,
                "backendId": "isabelle-local",
                "kind": "build",
                "target": {"kind": "theorem", "ref": "Main.demo"},
                "budget": {"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0},
            },
        )
        self.assertEqual(started["status"], "completed")
        polled = self.bridge.call_tool("backend.run.poll", {"runId": started["runId"]})
        logs = self.bridge.call_tool("backend.run.logs", {"runId": started["runId"]})
        artifacts = self.bridge.call_tool("backend.run.artifacts", {"runId": started["runId"]})
        self.assertEqual(polled["runId"], started["runId"])
        self.assertGreaterEqual(len(logs["logs"]), 1)
        self.assertGreaterEqual(len(artifacts["artifacts"]), 1)


if __name__ == "__main__":
    unittest.main()
