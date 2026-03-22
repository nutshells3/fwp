from __future__ import annotations

import json
import unittest

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_hub import build_reference_hub


class CrossBackendCompatibilityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()
        self.hub = build_reference_hub()
        self.hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}}})

    def open_workspace(self, backend_id: str) -> str:
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 2, "method": "workspace/open", "params": {"rootUri": (self.root / "examples" / "workspaces" / "demo").as_uri(), "backendId": backend_id}})
        return response["result"]["workspaceId"]

    def test_capability_matrix_exists(self) -> None:
        matrix = json.loads((self.root / "packages" / "formal-protocol" / "examples" / "capability-matrix.json").read_text(encoding="utf-8"))
        self.assertEqual(set(matrix["backends"]), {"isabelle", "lean", "rocq"})

    def test_unsupported_probes_fail_cleanly(self) -> None:
        lean_ws = self.open_workspace("lean-local")
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 3, "method": "probe/run", "params": {"workspaceId": lean_ws, "target": {"kind": "theorem", "ref": "Main.demo"}, "kind": "counterexample"}})
        self.assertEqual(response["error"]["code"], "CapabilityError")
        rocq_ws = self.open_workspace("rocq-local")
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 4, "method": "query/type", "params": {"workspaceId": rocq_ws, "target": {"kind": "theorem", "ref": "Main.demo"}}})
        self.assertEqual(response["error"]["code"], "CapabilityError")


if __name__ == "__main__":
    unittest.main()
