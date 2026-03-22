from __future__ import annotations

import unittest

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_hub import build_reference_hub


class IsabelleE2ETest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()
        self.hub = build_reference_hub()
        self.hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}}})
        workspace = self.hub.handle_request({"jsonrpc": "2.0", "id": 2, "method": "workspace/open", "params": {"rootUri": (self.root / "examples" / "workspaces" / "demo").as_uri(), "backendId": "isabelle-local"}})
        self.workspace_id = workspace["result"]["workspaceId"]
        self.hub.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "document/open",
                "params": {
                    "workspaceId": self.workspace_id,
                    "uri": (self.root / "examples" / "workspaces" / "demo" / "Main.thy").as_uri(),
                    "languageId": "isabelle",
                    "text": (self.root / "examples" / "workspaces" / "demo" / "Main.thy").read_text(encoding="utf-8"),
                },
            }
        )

    def rpc(self, method: str, params: dict) -> dict:
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 10, "method": method, "params": params})
        self.assertNotIn("error", response)
        return response["result"]

    def test_isabelle_end_to_end_surface(self) -> None:
        self.assertEqual(self.rpc("build/run", {"workspaceId": self.workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})["status"], "ok")
        self.assertEqual(self.rpc("query/goals", {"workspaceId": self.workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})["goals"][0]["goalId"], "isabelle_goal_1")
        self.assertEqual(self.rpc("probe/run", {"workspaceId": self.workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}, "kind": "counterexample", "implementation": {"tool": "nitpick"}})["kind"], "counterexample")
        self.assertEqual(self.rpc("probe/run", {"workspaceId": self.workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}, "kind": "proofSearch", "implementation": {"tool": "sledgehammer"}})["kind"], "proofSearch")
        self.assertTrue(self.rpc("audit/run", {"workspaceId": self.workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}, "include": ["trustFrontier", "dependencySlice", "contractPack"]})["contractPackRef"].startswith("contract-pack://"))
        self.assertEqual(self.rpc("backend/isabelle/ping", {"workspaceId": self.workspace_id})["backend"], "isabelle")


if __name__ == "__main__":
    unittest.main()
