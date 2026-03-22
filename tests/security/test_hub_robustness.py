from __future__ import annotations

import unittest

from scripts.dev.path_setup import activate, repo_root

activate()

from formal_hub.hub import build_reference_hub
from formal_hub.server import HttpPolicy


class HubRobustnessTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()
        self.hub = build_reference_hub()

    def rpc_error(self, method: str, params: dict) -> dict:
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
        self.assertIn("error", response)
        return response["error"]

    def test_malformed_jsonrpc_fails_predictably(self) -> None:
        response = self.hub.handle_request({"id": 1, "method": "ping", "params": {}})
        self.assertEqual(response["error"]["code"], "ProtocolError")

    def test_oversized_payload_is_rejected(self) -> None:
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {"blob": "x" * 250_000}})
        self.assertEqual(response["error"]["code"], "ResourceError")

    def test_fuzz_corpus_fails_with_stable_error_codes(self) -> None:
        corpus = {
            "hub_envelope": [
                ({"id": 1, "method": "ping", "params": {}}, "ProtocolError"),
                ({"jsonrpc": "2.0", "id": 1, "method": 9, "params": {}}, "ProtocolError"),
                ({"jsonrpc": "2.0", "id": 1, "method": "unknown/method", "params": {}}, "ProtocolError"),
            ],
            "hub_params": [
                ({"jsonrpc": "2.0", "id": 2, "method": "workspace/open", "params": {"backendId": "isabelle-local"}}, "ProtocolError"),
                ({"jsonrpc": "2.0", "id": 3, "method": "backend/capabilities", "params": {}}, "ProtocolError"),
                ({"jsonrpc": "2.0", "id": 4, "method": "probe/cancel", "params": {}}, "ProtocolError"),
                ({"jsonrpc": "2.0", "id": 5, "method": "query/goals", "params": {"workspaceId": "ws_demo", "target": {"kind": "theorem"}}}, "ProtocolError"),
            ],
        }
        for _, cases in corpus.items():
            for request, expected_code in cases:
                response = self.hub.handle_request(request)
                self.assertEqual(response["error"]["code"], expected_code)

    def test_invalid_run_backend_binding_fails_cleanly(self) -> None:
        self.hub.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2026-03-21", "clientInfo": {"name": "test", "version": "0.1.0"}, "capabilities": {}},
            }
        )
        workspace = self.hub.handle_request(
            {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "workspace/open",
                "params": {"rootUri": (self.root / "examples" / "workspaces" / "demo").as_uri(), "backendId": "isabelle-local"},
            }
        )["result"]
        error = self.rpc_error(
            "run.start",
            {
                "workspaceId": workspace["workspaceId"],
                "backendId": "lean-local",
                "kind": "build",
                "target": {"kind": "theorem", "ref": "Main.demo"},
                "budget": {"wall_ms": 5000, "idle_ms": 1000, "cancel_grace_ms": 500, "max_rss_mb": 512, "max_output_bytes": 1024, "max_diag_count": 32, "max_children": 2, "max_restarts": 0},
            },
        )
        self.assertEqual(error["code"], "WorkspaceError")

    def test_http_policy_requires_explicit_enablement_and_auth(self) -> None:
        policy = HttpPolicy(http_enabled=False)
        with self.assertRaises(PermissionError):
            policy.validate({})
        policy = HttpPolicy(http_enabled=True, auth_token="token", allowed_origins=["https://example.test"])
        with self.assertRaises(PermissionError):
            policy.validate({"Origin": "https://example.test"})
        policy.validate({"Origin": "https://example.test", "Authorization": "Bearer token"}, content_length=128, content_type="application/json")

    def test_http_policy_enforces_safe_defaults(self) -> None:
        policy = HttpPolicy(http_enabled=True, auth_token="token", allowed_origins=["https://example.test"], max_request_bytes=128)
        headers = {"Origin": "https://example.test", "Authorization": "Bearer token"}
        with self.assertRaises(ValueError):
            policy.validate(headers, content_length=16, content_type="text/plain")
        with self.assertRaises(ValueError):
            policy.validate(headers, content_length=256, content_type="application/json")
        response_headers = policy.response_headers(headers)
        self.assertEqual(response_headers["Cache-Control"], "no-store")
        self.assertEqual(response_headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response_headers["Access-Control-Allow-Origin"], "https://example.test")


if __name__ == "__main__":
    unittest.main()
