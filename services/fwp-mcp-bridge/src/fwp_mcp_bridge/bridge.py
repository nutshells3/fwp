from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from formal_protocol import MiniJsonSchemaValidator, ValidationError, load_schema, validate_exchange, validate_method_params, validate_method_result


class BridgePolicy:
    def __init__(self) -> None:
        self.allowed_tools = {
            "backend.list": "backend/list",
            "workspace.open": "workspace/open",
            "probe.run": "probe/run",
            "artifact.read": "artifact/read",
            "audit.run": "audit/run",
            "backend.run.start": "run.start",
            "backend.run.poll": "run.poll",
            "backend.run.cancel": "run.cancel",
            "backend.run.kill": "run.kill",
            "backend.run.logs": "run.logs",
            "backend.run.artifacts": "run.artifacts",
        }
        self.denied_methods = {
            "backend/discover",
            "document/open",
            "document/change",
            "backend/isabelle/raw",
            "backend/lean/raw",
            "backend/rocq/raw",
        }
        self.max_raw_bytes = 2048
        self.max_artifact_bytes = 4096
        self.redacted_placeholder = "[redacted]"

    def ensure_tool_allowed(self, tool_name: str) -> str:
        if tool_name not in self.allowed_tools:
            raise PermissionError(f"Tool not allowlisted: {tool_name}")
        return self.allowed_tools[tool_name]

    def sanitize_result(self, result: Any) -> Any:
        if isinstance(result, dict):
            sanitized = {}
            for key, value in result.items():
                lowered = key.lower()
                if key == "rawPayload":
                    encoded = json.dumps(value)
                    if len(encoded.encode("utf-8")) > self.max_raw_bytes:
                        sanitized[key] = {"redacted": True, "reason": "raw payload too large"}
                    else:
                        sanitized[key] = self.sanitize_result(value)
                elif lowered in {"argv", "env", "token", "authtoken", "authorization", "password", "secret"}:
                    if isinstance(value, list):
                        sanitized[key] = [self.redacted_placeholder]
                    elif isinstance(value, dict):
                        sanitized[key] = {"redacted": True}
                    else:
                        sanitized[key] = self.redacted_placeholder
                elif lowered == "endpoint":
                    sanitized[key] = self.redacted_placeholder
                else:
                    sanitized[key] = self.sanitize_result(value)
            return sanitized
        if isinstance(result, list):
            return [self.sanitize_result(item) for item in result]
        if isinstance(result, str) and ("secret" in result.lower() or ".." in result):
            return "[redacted]"
        return result


class MCPBridge:
    def __init__(self, hub: Any, *, repo_root: Path) -> None:
        self.hub = hub
        self.repo_root = repo_root
        self.policy = BridgePolicy()
        self.validator = MiniJsonSchemaValidator()

    def list_tools(self) -> list[dict[str, str]]:
        return [{"name": name, "method": method} for name, method in sorted(self.policy.allowed_tools.items())]

    def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        method = self.policy.ensure_tool_allowed(tool_name)
        try:
            validate_method_params(method, arguments)
        except ValidationError as exc:
            raise PermissionError(f"Invalid arguments for {tool_name}: {exc}") from exc
        response = self.hub.handle_request({"jsonrpc": "2.0", "id": 1, "method": method, "params": arguments})
        if "error" in response:
            raise PermissionError(response["error"]["message"])
        sanitized = self.policy.sanitize_result(response["result"])
        try:
            validate_method_result(method, sanitized)
        except ValidationError as exc:
            raise PermissionError(f"Bridge sanitized invalid output for {tool_name}: {exc}") from exc
        return sanitized

    def list_resources(self) -> list[str]:
        transcripts = sorted((self.repo_root / "packages" / "formal-protocol" / "examples" / "transcripts").glob("*.json"))
        descriptors = sorted((self.repo_root / "packages" / "formal-protocol" / "examples" / "descriptors").glob("*.json"))
        resources = [f"fwp://transcript/{path.stem}" for path in transcripts]
        resources.extend(f"fwp://descriptor/{path.stem}" for path in descriptors)
        return resources

    def read_resource(self, uri: str) -> dict[str, Any]:
        parsed = urlparse(uri)
        if parsed.scheme != "fwp":
            raise PermissionError("Unsupported resource scheme")
        parts = [part for part in parsed.path.split("/") if part]
        if parsed.netloc == "descriptor" and len(parts) == 1:
            path = self.repo_root / "packages" / "formal-protocol" / "examples" / "descriptors" / f"{parts[0]}.json"
            descriptor = json.loads(path.read_text(encoding="utf-8"))
            self.validator.validate(descriptor, load_schema("descriptor.schema.json")["$defs"]["Descriptor"])
            sanitized = self.policy.sanitize_result(descriptor)
            self.validator.validate(sanitized, load_schema("descriptor.schema.json")["$defs"]["Descriptor"])
            return sanitized
        if parsed.netloc == "transcript" and len(parts) == 1:
            path = self.repo_root / "packages" / "formal-protocol" / "examples" / "transcripts" / f"{parts[0]}.json"
            transcript = json.loads(path.read_text(encoding="utf-8"))
            validate_exchange(transcript)
            sanitized = self.policy.sanitize_result(transcript)
            validate_exchange(sanitized)
            return sanitized
        if parsed.netloc == "artifact" and len(parts) == 2:
            workspace_id, artifact_id = parts
            result = self.call_tool("artifact.read", {"workspaceId": workspace_id, "artifactId": artifact_id, "maxBytes": self.policy.max_artifact_bytes})
            return result
        raise PermissionError("Unsupported resource URI")
