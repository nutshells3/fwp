from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_hub import HubError, ReplayHarness, build_reference_hub
from formal_protocol import validate_exchange


class TranscriptReplayTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()
        self.hub = build_reference_hub()
        self.workspace_uri = (self.root / "examples" / "workspaces" / "demo").as_uri()
        self.document_uri = (self.root / "examples" / "workspaces" / "demo" / "Main.thy").as_uri()
        self.document_text = (self.root / "examples" / "workspaces" / "demo" / "Main.thy").read_text(encoding="utf-8")
        self.rpc("initialize", {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}})
        workspace = self.rpc("workspace/open", {"rootUri": self.workspace_uri, "backendId": "isabelle-local"})
        self.workspace_id = workspace["workspaceId"]
        self.rpc(
            "document/open",
            {
                "workspaceId": self.workspace_id,
                "uri": self.document_uri,
                "languageId": "isabelle",
                "text": self.document_text,
            },
        )

    def rpc(self, method: str, params: dict) -> dict:
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        self.assertNotIn("error", response, json.dumps(response, indent=2))
        return response["result"]

    def test_subscription_queues_receive_and_unsubscribe_clears(self) -> None:
        build_sub = self.rpc("event/subscribe", {"topic": "build/update"})
        goals_sub = self.rpc("event/subscribe", {"topic": "goals/update"})

        self.rpc("build/run", {"workspaceId": self.workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.rpc("query/goals", {"workspaceId": self.workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})

        build_events = self.hub.drain_subscription_events(build_sub["subscriptionId"])
        goals_events = self.hub.drain_subscription_events(goals_sub["subscriptionId"])
        self.assertEqual(build_events[0]["method"], "build/update")
        self.assertEqual(goals_events[0]["method"], "goals/update")

        self.rpc("event/unsubscribe", {"subscriptionId": build_sub["subscriptionId"]})
        with self.assertRaises(HubError):
            self.hub.drain_subscription_events(build_sub["subscriptionId"])

    def test_exported_transcript_replays_deterministically(self) -> None:
        for topic in ["build/update", "probe/update", "audit/update"]:
            self.rpc("event/subscribe", {"topic": topic})

        self.rpc("build/run", {"workspaceId": self.workspace_id, "target": {"kind": "theorem", "ref": "Main.demo"}})
        self.rpc(
            "probe/run",
            {
                "workspaceId": self.workspace_id,
                "target": {"kind": "theorem", "ref": "Main.demo"},
                "kind": "proofSearch",
                "implementation": {"tool": "sledgehammer"},
            },
        )
        self.rpc(
            "audit/run",
            {
                "workspaceId": self.workspace_id,
                "target": {"kind": "theorem", "ref": "Main.demo"},
                "include": ["trustFrontier", "dependencySlice", "contractPack"],
            },
        )

        with tempfile.TemporaryDirectory() as tempdir:
            transcript_path = Path(tempdir) / "captured-session.json"
            self.hub.recorder.export(transcript_path, "captured-session")
            transcript = json.loads(transcript_path.read_text(encoding="utf-8"))

        validate_exchange(transcript)
        harness = ReplayHarness(transcript)
        replayed_steps = [harness.next() for _ in transcript["steps"]]
        self.assertEqual(replayed_steps, transcript["steps"])
        self.assertGreaterEqual(len([step for step in replayed_steps if step["kind"] == "notification"]), 3)
        with self.assertRaises(IndexError):
            harness.next()


if __name__ == "__main__":
    unittest.main()
