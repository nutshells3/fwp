from __future__ import annotations

import json
import unittest

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_hub import build_reference_hub


class RunGovernanceConformanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()
        self.hub = build_reference_hub()
        self.hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}}})
        workspace = self.hub.handle_request({"jsonrpc": "2.0", "id": 2, "method": "workspace/open", "params": {"rootUri": (self.root / "examples" / "workspaces" / "demo").as_uri(), "backendId": "isabelle-local"}})
        self.workspace_id = workspace["result"]["workspaceId"]

    def rpc(self, method: str, params: dict) -> dict:
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 10, "method": method, "params": params})
        self.assertNotIn("error", response)
        return response["result"]

    def rpc_error(self, method: str, params: dict) -> dict:
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 10, "method": method, "params": params})
        self.assertIn("error", response)
        return response["error"]

    def test_initialize_exposes_governed_run_server_policy(self) -> None:
        init = self.hub.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 99,
                "method": "initialize",
                "params": {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}},
            }
        )["result"]
        self.assertEqual(init["capabilities"]["runGovernance"]["maxConcurrentRuns"], 4)
        self.assertEqual(init["capabilities"]["runGovernance"]["maxQueuedRuns"], 0)
        self.assertEqual(init["capabilities"]["runGovernance"]["requireExplicitBudget"], True)

    def test_governed_run_fixture_corpus_covers_required_scenarios(self) -> None:
        transcripts_dir = self.root / "packages" / "formal-protocol" / "examples" / "transcripts"
        required = {
            "11-run-timeout-isabelle.json",
            "12-run-cancel-lean.json",
            "13-run-kill-rocq.json",
            "15-run-idle-timeout-lean.json",
            "16-run-no-progress-isabelle.json",
            "17-run-cancel-escalate-kill-lean.json",
            "18-run-logs-after-kill-lean.json",
            "19-run-artifacts-after-kill-lean.json",
        }
        self.assertTrue(required <= {path.name for path in transcripts_dir.glob("*.json")})
        sample = json.loads((transcripts_dir / "17-run-cancel-escalate-kill-lean.json").read_text(encoding="utf-8"))
        self.assertEqual(sample["name"], "run-cancel-escalate-kill-lean")

    def test_success_timeout_cancel_kill_and_artifacts(self) -> None:
        success = self.rpc("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "build", "target": {"kind": "theorem", "ref": "Main.demo"}, "budget": {"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0}})
        self.assertEqual(success["status"], "completed")
        timeout = self.rpc("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "build", "target": {"kind": "theorem", "ref": "Main.demo"}, "budget": {"wall_ms": 1000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0}})
        self.assertEqual(timeout["status"], "timeout.wall")
        running = self.rpc("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "search", "target": {"kind": "theorem", "ref": "Main.long"}, "budget": {"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0}})
        cancelled = self.rpc("run.cancel", {"runId": running["runId"]})
        self.assertEqual(cancelled["status"], "aborted.user_requested")
        running = self.rpc("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "probe", "target": {"kind": "theorem", "ref": "Main.long"}, "budget": {"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0}})
        killed = self.rpc("run.kill", {"runId": running["runId"]})
        self.assertEqual(killed["status"], "killed")
        logs = self.rpc("run.logs", {"runId": success["runId"]})
        artifacts = self.rpc("run.artifacts", {"runId": success["runId"]})
        self.assertGreaterEqual(len(logs["logs"]), 1)
        self.assertGreaterEqual(len(artifacts["artifacts"]), 1)

    def test_idle_timeout_and_no_progress_divergence(self) -> None:
        budget = {"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0}
        idle = self.rpc("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "search", "target": {"kind": "theorem", "ref": "Main.stall"}, "budget": budget})
        self.assertEqual(idle["status"], "running")
        idle = self.rpc("run.poll", {"runId": idle["runId"]})
        self.assertEqual(idle["status"], "timeout.idle")
        self.assertEqual(idle["signals"][0]["kind"], "timeout.idle")

        no_progress = self.rpc("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "search", "target": {"kind": "theorem", "ref": "Main.noprogress"}, "budget": budget})
        self.assertEqual(no_progress["status"], "running")
        no_progress = self.rpc("run.poll", {"runId": no_progress["runId"]})
        self.assertEqual(no_progress["status"], "divergence.no_progress")
        self.assertEqual(no_progress["signals"][0]["kind"], "divergence.no_progress")

    def test_cancel_escalation_then_kill_preserves_logs_and_artifacts(self) -> None:
        budget = {"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0}
        stubborn = self.rpc("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "search", "target": {"kind": "theorem", "ref": "Main.stubborn"}, "budget": budget})
        self.assertEqual(stubborn["status"], "running")
        escalated = self.rpc("run.cancel", {"runId": stubborn["runId"]})
        self.assertEqual(escalated["status"], "running")
        self.assertEqual(escalated["signals"][0]["kind"], "abort.escalation_pending")
        killed = self.rpc("run.kill", {"runId": stubborn["runId"]})
        self.assertEqual(killed["status"], "killed")
        self.assertGreaterEqual(len(killed["artifactRefs"]), 1)
        logs = self.rpc("run.logs", {"runId": stubborn["runId"]})
        artifacts = self.rpc("run.artifacts", {"runId": stubborn["runId"]})
        self.assertIn("cooperative cancel timed out; escalation required", logs["logs"])
        self.assertGreaterEqual(len(artifacts["artifacts"]), 1)

    def test_concurrency_limit_rejects_fifth_running_job(self) -> None:
        budget = {"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0}
        run_ids = []
        for suffix in ["A", "B", "C", "D"]:
            result = self.rpc("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "search", "target": {"kind": "theorem", "ref": f"Main.long{suffix}"}, "budget": budget})
            run_ids.append(result["runId"])
            self.assertEqual(result["status"], "running")

        error = self.rpc_error("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "search", "target": {"kind": "theorem", "ref": "Main.longE"}, "budget": budget})
        self.assertEqual(error["code"], "ResourceError")
        self.assertEqual(error["retryable"], True)

        self.rpc("run.cancel", {"runId": run_ids[0]})
        resumed = self.rpc("run.start", {"workspaceId": self.workspace_id, "backendId": "isabelle-local", "kind": "search", "target": {"kind": "theorem", "ref": "Main.longF"}, "budget": budget})
        self.assertEqual(resumed["status"], "running")


if __name__ == "__main__":
    unittest.main()
