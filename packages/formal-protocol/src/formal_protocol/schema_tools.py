from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Tuple


class ValidationError(ValueError):
    pass


class MiniJsonSchemaValidator:
    def validate(self, instance: Any, schema: dict[str, Any], path: str = "$") -> None:
        schema_type = schema.get("type")
        if schema_type is not None:
            self._validate_type(instance, schema_type, path)

        if "const" in schema and instance != schema["const"]:
            raise ValidationError(f"{path}: expected const {schema['const']!r}")

        if "enum" in schema and instance not in schema["enum"]:
            raise ValidationError(f"{path}: value {instance!r} not in enum")

        if isinstance(instance, str) and "pattern" in schema:
            import re

            if re.fullmatch(schema["pattern"], instance) is None:
                raise ValidationError(f"{path}: string does not match pattern")

        if isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                raise ValidationError(f"{path}: below minimum")
            if "maximum" in schema and instance > schema["maximum"]:
                raise ValidationError(f"{path}: above maximum")

        if isinstance(instance, list):
            if "minItems" in schema and len(instance) < schema["minItems"]:
                raise ValidationError(f"{path}: too few items")
            items_schema = schema.get("items")
            if items_schema is not None:
                for index, item in enumerate(instance):
                    self.validate(item, items_schema, f"{path}[{index}]")

        if isinstance(instance, dict):
            required = schema.get("required", [])
            for key in required:
                if key not in instance:
                    raise ValidationError(f"{path}: missing required key {key!r}")
            properties = schema.get("properties", {})
            for key, value in instance.items():
                if key in properties:
                    self.validate(value, properties[key], f"{path}.{key}")
                elif schema.get("additionalProperties") is False:
                    raise ValidationError(f"{path}: unexpected property {key!r}")

    def _validate_type(self, instance: Any, expected: str, path: str) -> None:
        checks = {
            "object": lambda value: isinstance(value, dict),
            "array": lambda value: isinstance(value, list),
            "string": lambda value: isinstance(value, str),
            "integer": lambda value: isinstance(value, int) and not isinstance(value, bool),
            "number": lambda value: isinstance(value, (int, float)) and not isinstance(value, bool),
            "boolean": lambda value: isinstance(value, bool),
            "null": lambda value: value is None,
        }
        check = checks.get(expected)
        if check is None:
            raise ValidationError(f"{path}: unsupported schema type {expected}")
        if not check(instance):
            raise ValidationError(f"{path}: expected {expected}, got {type(instance).__name__}")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def schema_dir() -> Path:
    return _repo_root() / "packages" / "formal-protocol" / "schemas"


def example_dir() -> Path:
    return _repo_root() / "packages" / "formal-protocol" / "examples"


def load_schema(name: str) -> dict[str, Any]:
    return json.loads((schema_dir() / name).read_text(encoding="utf-8"))


SchemaRef = Tuple[str, str]


METHOD_SCHEMA_MAP: dict[str, tuple[SchemaRef | None, SchemaRef | None]] = {
    "initialize": (("initialize.schema.json", "InitializeParams"), ("initialize.schema.json", "InitializeResult")),
    "initialized": (("methods.schema.json", "EmptyParams"), ("results.schema.json", "AckResult")),
    "shutdown": (("methods.schema.json", "EmptyParams"), ("results.schema.json", "ShutdownResult")),
    "exit": (("methods.schema.json", "EmptyParams"), ("results.schema.json", "ExitResult")),
    "ping": (("methods.schema.json", "EmptyParams"), ("results.schema.json", "PingResult")),
    "backend/list": (("methods.schema.json", "EmptyParams"), None),
    "backend/discover": (("methods.schema.json", "BackendDiscoverParams"), None),
    "backend/capabilities": (("methods.schema.json", "BackendIdParams"), ("results.schema.json", "BackendCapabilitiesResult")),
    "backend/describe": (("methods.schema.json", "BackendIdParams"), None),
    "workspace/open": (("methods.schema.json", "WorkspaceOpenParams"), ("entities.schema.json", "WorkspaceHandle")),
    "workspace/configure": (("methods.schema.json", "WorkspaceConfigureParams"), ("results.schema.json", "WorkspaceConfigureResult")),
    "workspace/close": (("methods.schema.json", "WorkspaceIdParams"), ("results.schema.json", "WorkspaceCloseResult")),
    "document/open": (("methods.schema.json", "DocumentOpenParams"), ("entities.schema.json", "DocumentHandle")),
    "document/change": (("methods.schema.json", "DocumentChangeParams"), ("entities.schema.json", "DocumentHandle")),
    "document/save": (("methods.schema.json", "DocumentSaveParams"), ("entities.schema.json", "SnapshotRef")),
    "document/close": (("methods.schema.json", "DocumentCloseParams"), ("results.schema.json", "DocumentCloseResult")),
    "target/list": (("methods.schema.json", "WorkspaceIdParams"), ("results.schema.json", "TargetListResult")),
    "build/run": (("methods.schema.json", "BuildRunParams"), ("results.schema.json", "BuildRunResult")),
    "build/cancel": (("methods.schema.json", "BuildCancelParams"), ("results.schema.json", "BuildCancelResult")),
    "artifact/list": (("methods.schema.json", "WorkspaceIdParams"), ("results.schema.json", "ArtifactListResult")),
    "artifact/read": (("methods.schema.json", "ArtifactReadParams"), ("results.schema.json", "ArtifactReadResult")),
    "artifact/export": (("methods.schema.json", "ArtifactExportParams"), ("results.schema.json", "ArtifactExportResult")),
    "query/goals": (("methods.schema.json", "QueryParams"), ("results.schema.json", "QueryGoalsResult")),
    "query/hover": (("methods.schema.json", "QueryParams"), ("results.schema.json", "QueryHoverResult")),
    "query/definition": (("methods.schema.json", "QueryParams"), ("results.schema.json", "QueryDefinitionResult")),
    "query/type": (("methods.schema.json", "QueryParams"), ("results.schema.json", "QueryTypeResult")),
    "query/dependencies": (("methods.schema.json", "QueryParams"), ("results.schema.json", "DependencySlice")),
    "query/diagnostics": (
        ("methods.schema.json", "QueryParams"),
        ("results.schema.json", "QueryDiagnosticsResult"),
    ),
    "query/status": (("methods.schema.json", "QueryParams"), ("results.schema.json", "QueryStatusResult")),
    "probe/run": (("methods.schema.json", "ProbeRunParams"), ("results.schema.json", "ProbeRunResult")),
    "probe/cancel": (("methods.schema.json", "ProbeCancelParams"), ("results.schema.json", "ProbeCancelResult")),
    "probe/results": (("methods.schema.json", "ProbeResultsParams"), ("results.schema.json", "ProbeResultsResult")),
    "audit/run": (("methods.schema.json", "AuditRunParams"), ("results.schema.json", "AuditSignalBundle")),
    "audit/signals": (("methods.schema.json", "AuditSignalsParams"), ("results.schema.json", "AuditSignalsResult")),
    "audit/profile": (("methods.schema.json", "AuditRunParams"), ("results.schema.json", "AuditProfileResult")),
    "audit/contractPack": (("methods.schema.json", "AuditRunParams"), ("results.schema.json", "AuditContractPackResult")),
    "event/subscribe": (("methods.schema.json", "EventSubscribeParams"), ("results.schema.json", "EventSubscribeResult")),
    "event/unsubscribe": (("methods.schema.json", "EventUnsubscribeParams"), ("results.schema.json", "EventUnsubscribeResult")),
    "run.start": (("run-governance.schema.json", "RunStartParams"), ("run-governance.schema.json", "RunStatus")),
    "run.poll": (("run-governance.schema.json", "RunPollParams"), ("run-governance.schema.json", "RunStatus")),
    "run.cancel": (("run-governance.schema.json", "RunPollParams"), ("run-governance.schema.json", "RunStatus")),
    "run.kill": (("run-governance.schema.json", "RunPollParams"), ("run-governance.schema.json", "RunStatus")),
    "run.logs": (("run-governance.schema.json", "RunPollParams"), ("run-governance.schema.json", "RunLogsResult")),
    "run.artifacts": (
        ("run-governance.schema.json", "RunPollParams"),
        ("run-governance.schema.json", "RunArtifactsResult"),
    ),
}


def _schema_def(file_name: str, definition_name: str) -> dict[str, Any]:
    return load_schema(file_name)["$defs"][definition_name]


NOTIFICATION_SCHEMA_MAP: dict[str, SchemaRef] = {
    "build/update": ("events.schema.json", "BuildUpdateParams"),
    "goals/update": ("events.schema.json", "GoalsUpdateParams"),
    "diagnostics/update": ("events.schema.json", "DiagnosticsUpdateParams"),
    "probe/update": ("events.schema.json", "ProbeUpdateParams"),
    "audit/update": ("events.schema.json", "AuditUpdateParams"),
}


def _method_schema(method: str, index: int) -> dict[str, Any] | None:
    references = METHOD_SCHEMA_MAP.get(method)
    if references is None:
        return None
    reference = references[index]
    if reference is None:
        return None
    return _schema_def(*reference)


def validate_method_params(method: str, params: dict[str, Any]) -> None:
    schema = _method_schema(method, 0)
    if schema is None:
        return
    MiniJsonSchemaValidator().validate(params, schema)


def validate_method_result(method: str, result: Any) -> None:
    schema = _method_schema(method, 1)
    if schema is None:
        return
    MiniJsonSchemaValidator().validate(result, schema)


def validate_notification(method: str, params: dict[str, Any]) -> None:
    reference = NOTIFICATION_SCHEMA_MAP.get(method)
    if reference is None:
        return
    MiniJsonSchemaValidator().validate(params, _schema_def(*reference))


def validate_exchange(exchange: dict[str, Any]) -> None:
    validator = MiniJsonSchemaValidator()
    validator.validate(
        exchange,
        {
            "type": "object",
            "required": ["name", "steps"],
            "properties": {
                "name": {"type": "string"},
                "steps": {"type": "array", "minItems": 1, "items": {"type": "object"}},
            },
            "additionalProperties": True,
        },
    )
    for step in exchange["steps"]:
        message = step["message"]
        if step["kind"] == "request":
            validator.validate(
                message,
                {
                    "type": "object",
                    "required": ["jsonrpc", "id", "method", "params"],
                    "properties": {
                        "jsonrpc": {"type": "string", "const": "2.0"},
                        "id": {"type": "integer"},
                        "method": {"type": "string"},
                        "params": {"type": "object"},
                    },
                    "additionalProperties": True,
                },
            )
            method = message["method"]
            schema = _method_schema(method, 0)
            if schema is not None:
                validator.validate(message["params"], schema)
        elif step["kind"] == "response":
            validator.validate(
                message,
                {
                    "type": "object",
                    "required": ["jsonrpc", "id"],
                    "properties": {
                        "jsonrpc": {"type": "string", "const": "2.0"},
                        "id": {"type": "integer"},
                    },
                    "additionalProperties": True,
                },
            )
            if "result" in message:
                method = step.get("forMethod")
                schema = _method_schema(method, 1) if method is not None else None
                if schema is not None:
                    validator.validate(message["result"], schema)
        elif step["kind"] == "notification":
            validator.validate(
                message,
                {
                    "type": "object",
                    "required": ["jsonrpc", "method", "params"],
                    "properties": {
                        "jsonrpc": {"type": "string", "const": "2.0"},
                        "method": {"type": "string"},
                        "params": {"type": "object"},
                    },
                    "additionalProperties": True,
                },
            )
            validate_notification(message["method"], message["params"])
