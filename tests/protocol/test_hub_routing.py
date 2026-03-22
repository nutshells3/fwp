from __future__ import annotations

import json
import unittest

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_hub import build_reference_hub


class HubRoutingTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()
        self.hub = build_reference_hub()
        self.workspace_uri = (self.root / "examples" / "workspaces" / "demo").as_uri()

    def rpc(self, method: str, params: dict) -> dict:
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        self.assertNotIn("error", response, json.dumps(response, indent=2))
        return response["result"]

    def test_initialize_and_backend_list(self) -> None:
        result = self.rpc("initialize", {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}})
        self.assertEqual(result["protocolVersion"], "2026-03-21")
        backends = self.rpc("backend/list", {})
        self.assertEqual({item["kind"] for item in backends}, {"isabelle", "lean", "rocq"})

    def test_workspace_document_build_query_probe_audit_flow(self) -> None:
        self.rpc("initialize", {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}})
        workspace = self.rpc("workspace/open", {"rootUri": self.workspace_uri, "backendId": "isabelle-local"})
        document = self.rpc(
            "document/open",
            {
                "workspaceId": workspace["workspaceId"],
                "uri": (self.root / "examples" / "workspaces" / "demo" / "Main.thy").as_uri(),
                "languageId": "isabelle",
                "text": (self.root / "examples" / "workspaces" / "demo" / "Main.thy").read_text(encoding="utf-8"),
            },
        )
        self.assertEqual(document["version"], 1)
        goals = self.rpc("query/goals", {"workspaceId": workspace["workspaceId"], "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.assertEqual(len(goals["goals"]), 1)
        build = self.rpc("build/run", {"workspaceId": workspace["workspaceId"], "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.assertEqual(build["status"], "ok")
        probe = self.rpc(
            "probe/run",
            {
                "workspaceId": workspace["workspaceId"],
                "target": {"kind": "theorem", "ref": "Main.demo"},
                "kind": "proofSearch",
                "implementation": {"tool": "sledgehammer"},
            },
        )
        self.assertEqual(probe["status"], "completed")
        audit = self.rpc(
            "audit/run",
            {
                "workspaceId": workspace["workspaceId"],
                "target": {"kind": "theorem", "ref": "Main.demo"},
                "include": ["trustFrontier", "dependencySlice", "contractPack"],
            },
        )
        self.assertTrue(audit["contractPackRef"].startswith("contract-pack://"))
        artifact = self.rpc(
            "artifact/read",
            {"workspaceId": workspace["workspaceId"], "artifactId": build["artifacts"][0]["artifactId"], "maxBytes": 512},
        )
        self.assertFalse(artifact["truncated"])


if __name__ == "__main__":
    unittest.main()
