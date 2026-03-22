from __future__ import annotations

import json
import unittest
from unittest.mock import patch

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_hub import build_reference_hub
from fwp_client import (
    HttpHubTransport,
    LocalHubTransport,
    ProofAuditRequest,
    ProofBuildRequest,
    ProofProtocolClient,
    ProofWorkspaceInputs,
    WorkspaceDocumentInput,
)


class _FakeHttpResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self) -> "_FakeHttpResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class ProofProtocolClientTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()
        self.hub = build_reference_hub()
        self.client = ProofProtocolClient(LocalHubTransport(self.hub))
        self.workspace_inputs = ProofWorkspaceInputs(
            root_uri=(self.root / "examples" / "workspaces" / "demo").as_uri(),
            documents=[
                WorkspaceDocumentInput(
                    uri=(self.root / "examples" / "workspaces" / "demo" / "Main.thy").as_uri(),
                    language_id="isabelle",
                    text=(self.root / "examples" / "workspaces" / "demo" / "Main.thy").read_text(encoding="utf-8"),
                )
            ],
        )

    def test_submit_formalization_check_and_workspace_access(self) -> None:
        status = self.client.submit_formalization_check(
            ProofBuildRequest(
                request_id="req-build-1",
                project_id="project-1",
                subject_id="claim-1",
                subject_revision_id="rev-1",
                artifact_ref="artifact://formal-claim/claim-1",
                proof_source="foundational claim text",
                theorem_statement="claim 1",
                target_backend="isabelle-local",
                module_name="Main",
                primary_target="demo",
                workspace_inputs=self.workspace_inputs,
                resource_policy={"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0},
                lineage={"sourceDocumentRef": "doc://claim-1"},
            )
        )
        self.assertEqual(status.status, "completed")
        self.assertEqual(status.lineage["subjectId"], "claim-1")
        self.assertEqual(status.backend_extensions["backend"], "isabelle")

        snapshot = self.client.get_workspace_snapshot(status.workspace_ref)
        self.assertEqual(snapshot.backend_id, "isabelle-local")
        self.assertGreaterEqual(len(snapshot.targets), 1)
        self.assertGreaterEqual(len(snapshot.artifacts), 1)

        artifacts = self.client.list_artifacts(status.workspace_ref)
        self.assertGreaterEqual(len(artifacts.artifacts), 1)
        artifact = self.client.read_artifact(status.workspace_ref, artifacts.artifacts[0]["artifactId"])
        self.assertIn("build", artifact.content.lower())
        self.assertIn(artifact.source, {"artifact/read", "run.logs-fallback"})

    def test_submit_audit_and_job_control_paths(self) -> None:
        audit = self.client.submit_audit_probe(
            ProofAuditRequest(
                request_id="req-audit-1",
                project_id="project-1",
                subject_id="claim-2",
                subject_revision_id="rev-2",
                artifact_ref="artifact://formal-claim/claim-2",
                proof_source="auditable claim text",
                theorem_statement="claim 2",
                target_backend="isabelle-local",
                module_name="Main",
                primary_target="demo",
                workspace_inputs=self.workspace_inputs,
                resource_policy={"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0},
                lineage={"sourceDocumentRef": "doc://claim-2"},
                trust_frontier_requirements=["trustFrontier"],
                probe_requirements=["dependencySlice"],
                export_requirements=["contractPack"],
            )
        )
        self.assertTrue(audit.contract_pack_ref.startswith("contract-pack://"))
        self.assertEqual(audit.lineage["subjectId"], "claim-2")

        stubborn = self.client.submit_formalization_check(
            ProofBuildRequest(
                request_id="req-build-2",
                project_id="project-1",
                subject_id="claim-3",
                subject_revision_id="rev-3",
                artifact_ref="artifact://formal-claim/claim-3",
                proof_source="search claim text",
                theorem_statement="claim 3",
                target_backend="isabelle-local",
                module_name="Main",
                primary_target="stubborn",
                workspace_inputs=self.workspace_inputs,
                resource_policy={"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0},
                lineage={"sourceDocumentRef": "doc://claim-3"},
                run_kind="search",
            )
        )
        self.assertEqual(stubborn.status, "running")
        pending = self.client.cancel_job(stubborn.job_id)
        self.assertEqual(pending.status, "running")
        self.assertEqual(pending.termination_reason, None)
        killed = self.client.kill_job(stubborn.job_id)
        self.assertEqual(killed.status, "killed")
        self.assertGreaterEqual(len(killed.artifact_refs), 1)
        postmortem = self.client.read_artifact(stubborn.workspace_ref, killed.artifact_refs[0]["artifactId"])
        self.assertIn("killed", postmortem.content.lower())
        self.assertFalse(postmortem.canonical)
        self.assertEqual(postmortem.source, "run.logs-fallback")

    def test_http_transport_builds_jsonrpc_request(self) -> None:
        transport = HttpHubTransport("http://fwp.test/rpc", auth_token="secret-token", origin="https://caller.test", timeout_seconds=2.0)
        with patch("fwp_client.client.urlopen", return_value=_FakeHttpResponse({"jsonrpc": "2.0", "id": 1, "result": {"pong": True}})) as mocked:
            result = transport.call("ping", {})
        self.assertEqual(result["pong"], True)
        request = mocked.call_args.args[0]
        body = json.loads(request.data.decode("utf-8"))
        headers = {key.lower(): value for key, value in request.header_items()}
        self.assertEqual(body["method"], "ping")
        self.assertEqual(headers["authorization"], "Bearer secret-token")
        self.assertEqual(headers["origin"], "https://caller.test")


if __name__ == "__main__":
    unittest.main()
