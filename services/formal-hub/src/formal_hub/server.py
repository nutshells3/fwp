from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .hub import build_reference_hub


def _activate_sibling_proof_assistant() -> None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent.parent.parent.parent / "proof-assistant" / "src"
        if candidate.exists():
            text = str(candidate)
            if text not in sys.path:
                sys.path.insert(0, text)
            return


_activate_sibling_proof_assistant()

try:
    from proof_assistant.server import HttpPolicy as HttpPolicy  # type: ignore
except Exception:  # pragma: no cover - standalone fallback
    class HttpPolicy:
        def __init__(
            self,
            *,
            http_enabled: bool = False,
            auth_token: str | None = None,
            allowed_origins: list[str] | None = None,
            max_request_bytes: int = 200_000,
            read_timeout_seconds: int = 5,
        ):
            self.http_enabled = http_enabled
            self.auth_token = auth_token
            self.allowed_origins = allowed_origins or []
            self.max_request_bytes = max_request_bytes
            self.read_timeout_seconds = read_timeout_seconds

        def validate(self, headers: dict[str, str], *, content_length: int | None = None, content_type: str | None = None) -> None:
            if not self.http_enabled:
                raise PermissionError("HTTP mode is disabled")
            origin = headers.get("Origin")
            if self.allowed_origins and origin not in self.allowed_origins:
                raise PermissionError("Origin not allowed")
            if self.auth_token is not None and headers.get("Authorization") != f"Bearer {self.auth_token}":
                raise PermissionError("Missing or invalid Authorization header")
            if content_type is not None and not content_type.startswith("application/json"):
                raise ValueError("Content-Type must be application/json")
            if content_length is not None and content_length > self.max_request_bytes:
                raise ValueError("Request body too large")

        def response_headers(self, headers: dict[str, str]) -> dict[str, str]:
            response_headers = {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
            }
            origin = headers.get("Origin")
            if self.allowed_origins and origin in self.allowed_origins:
                response_headers["Access-Control-Allow-Origin"] = origin
                response_headers["Vary"] = "Origin"
            return response_headers


def serve_http(*, host: str = "127.0.0.1", port: int = 8765, auth_token: str | None = None, allowed_origins: list[str] | None = None) -> None:
    hub = build_reference_hub()
    policy = HttpPolicy(http_enabled=True, auth_token=auth_token, allowed_origins=allowed_origins)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            try:
                header_map = {key: value for key, value in self.headers.items()}
                self.connection.settimeout(policy.read_timeout_seconds)
                length = int(self.headers.get("Content-Length", "0"))
                policy.validate(header_map, content_length=length, content_type=self.headers.get("Content-Type", ""))
                request = json.loads(self.rfile.read(length).decode("utf-8"))
                response = hub.handle_request(request)
                payload = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                for key, value in policy.response_headers(header_map).items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(payload)
            except PermissionError as exc:
                self.send_error(403, str(exc))
            except json.JSONDecodeError as exc:
                self.send_error(400, f"Invalid JSON payload: {exc.msg}")
            except ValueError as exc:
                status = 413 if "too large" in str(exc).lower() else 400
                self.send_error(status, str(exc))
            except Exception as exc:  # pragma: no cover
                self.send_error(500, str(exc))

        def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
            return

    httpd = ThreadingHTTPServer((host, port), Handler)
    httpd.timeout = policy.read_timeout_seconds
    httpd.serve_forever()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--http-enable", action="store_true")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--auth-token")
    parser.add_argument("--allow-origin", action="append", default=[])
    args = parser.parse_args()
    if args.http_enable:
        serve_http(
            host=args.host,
            port=args.port,
            auth_token=args.auth_token,
            allowed_origins=args.allow_origin,
        )
    else:
        hub = build_reference_hub()
        print(json.dumps(hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": "ping", "params": {}})))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
