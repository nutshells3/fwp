from __future__ import annotations

import unittest

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_hub import build_reference_hub


class SecondaryBackendE2ETest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()
        self.hub = build_reference_hub()
        self.hub.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}},
            }
        )

    def open_workspace(self, backend_id: str, file_name: str, language_id: str) -> str:
        workspace = self.hub.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "workspace/open",
                "params": {"rootUri": (self.root / "examples" / "workspaces" / "demo").as_uri(), "backendId": backend_id},
            }
        )["result"]
        self.hub.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "document/open",
                "params": {
                    "workspaceId": workspace["workspaceId"],
                    "uri": (self.root / "examples" / "workspaces" / "demo" / file_name).as_uri(),
                    "languageId": language_id,
                    "text": (self.root / "examples" / "workspaces" / "demo" / file_name).read_text(encoding="utf-8"),
                },
            }
        )
        return workspace["workspaceId"]

    def rpc(self, method: str, params: dict) -> dict:
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 10, "method": method, "params": params})
        self.assertNotIn("error", response)
        return response["result"]

    def test_lean_end_to_end_surface(self) -> None:
        workspace_id = self.open_workspace("lean-local", "Main.lean", "lean")
        build = self.rpc("build/run", {"workspaceId": workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.assertEqual(build["status"], "ok")
        goals = self.rpc("query/goals", {"workspaceId": workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.assertEqual(goals["goals"][0]["goalId"], "lean_goal_1")
        query_type = self.rpc("query/type", {"workspaceId": workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.assertEqual(query_type["type"], "Prop")
        probe = self.rpc(
            "probe/run",
            {
                "workspaceId": workspace_id,
                "target": {"kind": "theorem", "ref": "Main.demo"},
                "kind": "proofSearch",
                "implementation": {"tool": "aesop"},
            },
        )
        self.assertEqual(probe["kind"], "proofSearch")
        self.assertEqual(self.rpc("backend/lean/ping", {"workspaceId": workspace_id})["backend"], "lean")

    def test_rocq_end_to_end_surface(self) -> None:
        workspace_id = self.open_workspace("rocq-local", "Main.v", "rocq")
        build = self.rpc("build/run", {"workspaceId": workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.assertEqual(build["status"], "ok")
        goals = self.rpc("query/goals", {"workspaceId": workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.assertEqual(goals["goals"][0]["goalId"], "rocq_goal_1")
        dependencies = self.rpc("query/dependencies", {"workspaceId": workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.assertGreaterEqual(len(dependencies["dependencies"]), 1)
        probe = self.rpc(
            "probe/run",
            {
                "workspaceId": workspace_id,
                "target": {"kind": "theorem", "ref": "Main.demo"},
                "kind": "proofSearch",
                "implementation": {"tool": "petanque"},
            },
        )
        self.assertEqual(probe["kind"], "proofSearch")
        self.assertEqual(self.rpc("backend/rocq/ping", {"workspaceId": workspace_id})["backend"], "rocq")


if __name__ == "__main__":
    unittest.main()
