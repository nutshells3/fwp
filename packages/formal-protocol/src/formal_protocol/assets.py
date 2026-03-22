from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PROTOCOL_VERSION = "2026-03-21"
SCHEMA_URI = "https://json-schema.org/draft/2020-12/schema"
BACKEND_LANGUAGE_IDS: dict[str, tuple[str, ...]] = {
    "isabelle": ("isabelle", "isabelle-root"),
    "lean": ("lean",),
    "rocq": ("rocq", "coq"),
}
RUN_BUDGET_REQUIRED_FIELDS: tuple[str, ...] = (
    "wall_ms",
    "idle_ms",
    "cancel_grace_ms",
    "max_rss_mb",
    "max_output_bytes",
    "max_diag_count",
    "max_children",
    "max_restarts",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _schemas_dir() -> Path:
    return _repo_root() / "packages" / "formal-protocol" / "schemas"


def _examples_dir() -> Path:
    return _repo_root() / "packages" / "formal-protocol" / "examples"


def _docs_dir() -> Path:
    return _repo_root() / "docs" / "protocol"


def _workspace_dir() -> Path:
    return _repo_root() / "examples" / "workspaces" / "demo"


def accepted_language_ids(kind: str) -> tuple[str, ...]:
    return BACKEND_LANGUAGE_IDS.get(kind, (kind,))


def backend_capabilities(kind: str) -> dict[str, Any]:
    return {
        "workspaceDiscovery": True,
        "documentSync": {"mode": "incremental"},
        "buildTargets": True,
        "queries": {
            "goals": True,
            "hover": True,
            "definition": True,
            "type": kind != "rocq",
            "dependencies": True,
            "diagnostics": True,
            "status": True,
        },
        "probes": {
            "counterexample": kind == "isabelle",
            "proofSearch": True,
            "replay": kind == "isabelle",
            "premiseDeletion": kind == "isabelle",
            "conclusionPerturbation": kind == "isabelle",
            "consistencyCheck": False,
            "dependencySlice": True,
            "buildReplay": kind == "isabelle",
        },
        "auditSignals": {
            "trustFrontier": kind == "isabelle",
            "rawBackendPayload": True,
            "contractPack": True,
        },
        "subscriptions": {
            "progress": True,
            "diagnostics": True,
            "goals": True,
            "audit": True,
        },
        "runGovernance": {
            "supports_run_jobs": True,
            "supports_cancel": True,
            "supports_kill": True,
            "supports_heartbeat_budget": kind == "lean",
            "supports_progress_events": True,
            "supports_raw_backend_handles": False,
            "require_explicit_budget": True,
            "max_concurrent_runs": 4,
            "max_queued_runs": 0,
        },
        "experimental": {f"backend/{kind}/nativeExtensions": True},
    }

def default_server_policy(*, max_concurrent: int = 4) -> dict[str, Any]:
    return {
        "requireExplicitBudget": True,
        "maxConcurrentRuns": max_concurrent,
        "maxQueuedRuns": 0,
        "defaultCancelMode": "cooperative-then-kill",
    }


def default_run_budget() -> dict[str, int]:
    return {
        "wall_ms": 5000,
        "idle_ms": 1500,
        "cancel_grace_ms": 500,
        "max_rss_mb": 512,
        "max_output_bytes": 32768,
        "max_diag_count": 128,
        "max_children": 2,
        "max_restarts": 0,
    }


def run_budget_required_fields() -> tuple[str, ...]:
    return RUN_BUDGET_REQUIRED_FIELDS


def _empty_object_schema() -> dict[str, Any]:
    return {"type": "object", "additionalProperties": False}


def _target_ref_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["kind", "ref"],
        "properties": {
            "kind": {"type": "string"},
            "ref": {"type": "string"},
            "workspaceId": {"type": "string"},
            "documentId": {"type": "string"},
        },
        "additionalProperties": True,
    }


def _artifact_ref_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["artifactId", "kind", "uri"],
        "properties": {
            "artifactId": {"type": "string"},
            "kind": {"type": "string"},
            "uri": {"type": "string"},
        },
        "additionalProperties": True,
    }


def _signal_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": ["kind"],
        "properties": {"kind": {"type": "string"}},
        "additionalProperties": True,
    }


def _run_budget_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "required": [
            "wall_ms",
            "idle_ms",
            "cancel_grace_ms",
            "max_rss_mb",
            "max_output_bytes",
            "max_diag_count",
            "max_children",
            "max_restarts",
        ],
        "properties": {
            "wall_ms": {"type": "integer", "minimum": 1},
            "idle_ms": {"type": "integer", "minimum": 1},
            "cancel_grace_ms": {"type": "integer", "minimum": 1},
            "max_rss_mb": {"type": "integer", "minimum": 1},
            "max_output_bytes": {"type": "integer", "minimum": 1},
            "max_diag_count": {"type": "integer", "minimum": 1},
            "max_children": {"type": "integer", "minimum": 0},
            "max_restarts": {"type": "integer", "minimum": 0},
            "backendHints": {"type": "object", "additionalProperties": True},
        },
        "additionalProperties": False,
    }


def schema_documents() -> dict[str, dict[str, Any]]:
    return {
        "initialize.schema.json": {
            "$schema": SCHEMA_URI,
            "title": "FWP Initialize Schemas",
            "type": "object",
            "$defs": {
                "InitializeParams": {
                    "type": "object",
                    "required": ["protocolVersion", "clientInfo", "capabilities"],
                    "properties": {
                        "protocolVersion": {"type": "string", "pattern": r"\d{4}-\d{2}-\d{2}"},
                        "clientInfo": {
                            "type": "object",
                            "required": ["name", "version"],
                            "properties": {"name": {"type": "string"}, "version": {"type": "string"}},
                            "additionalProperties": False,
                        },
                        "capabilities": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
                "InitializeResult": {
                    "type": "object",
                    "required": ["protocolVersion", "serverInfo", "capabilities"],
                    "properties": {
                        "protocolVersion": {"type": "string", "pattern": r"\d{4}-\d{2}-\d{2}"},
                        "serverInfo": {
                            "type": "object",
                            "required": ["name", "version"],
                            "properties": {"name": {"type": "string"}, "version": {"type": "string"}},
                            "additionalProperties": False,
                        },
                        "capabilities": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
            },
        },
        "entities.schema.json": {
            "$schema": SCHEMA_URI,
            "title": "FWP Entity Schemas",
            "type": "object",
            "$defs": {
                "BackendDescriptor": {
                    "type": "object",
                    "required": ["backendId", "kind", "displayName", "version", "protocolVersion", "languages", "capabilities", "transport"],
                    "properties": {
                        "backendId": {"type": "string"},
                        "kind": {"type": "string"},
                        "displayName": {"type": "string"},
                        "version": {"type": "string"},
                        "protocolVersion": {"type": "string"},
                        "languages": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        "capabilities": {"type": "object", "additionalProperties": True},
                        "transport": {"type": "object", "additionalProperties": True},
                        "argv": {"type": "array", "items": {"type": "string"}},
                    },
                    "additionalProperties": True,
                },
                "WorkspaceHandle": {
                    "type": "object",
                    "required": ["workspaceId", "rootUri", "backendId", "connectionSource", "openedAt"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "rootUri": {"type": "string"},
                        "backendId": {"type": "string"},
                        "connectionSource": {"type": "string"},
                        "openedAt": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "DocumentHandle": {
                    "type": "object",
                    "required": ["documentId", "workspaceId", "uri", "languageId", "version", "syncMode"],
                    "properties": {
                        "documentId": {"type": "string"},
                        "workspaceId": {"type": "string"},
                        "uri": {"type": "string"},
                        "languageId": {"type": "string"},
                        "version": {"type": "integer", "minimum": 0},
                        "syncMode": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "TargetRef": {
                    "type": "object",
                    "required": ["kind", "ref"],
                    "properties": {
                        "kind": {"type": "string"},
                        "ref": {"type": "string"},
                        "workspaceId": {"type": "string"},
                        "documentId": {"type": "string"},
                    },
                    "additionalProperties": True,
                },
                "SnapshotRef": {
                    "type": "object",
                    "required": ["snapshotId", "workspaceId"],
                    "properties": {
                        "snapshotId": {"type": "string"},
                        "workspaceId": {"type": "string"},
                        "documentId": {"type": "string"},
                        "backendOpaqueRef": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
            },
        },
        "methods.schema.json": {
            "$schema": SCHEMA_URI,
            "title": "FWP Method Schemas",
            "type": "object",
            "$defs": {
                "EmptyParams": _empty_object_schema(),
                "WorkspaceIdParams": {
                    "type": "object",
                    "required": ["workspaceId"],
                    "properties": {"workspaceId": {"type": "string"}},
                    "additionalProperties": False,
                },
                "BackendIdParams": {
                    "type": "object",
                    "required": ["backendId"],
                    "properties": {"backendId": {"type": "string"}},
                    "additionalProperties": False,
                },
                "BackendDiscoverParams": {
                    "type": "object",
                    "required": ["rootUri"],
                    "properties": {"rootUri": {"type": "string"}},
                    "additionalProperties": False,
                },
                "WorkspaceOpenParams": {
                    "type": "object",
                    "required": ["rootUri", "backendId"],
                    "properties": {"rootUri": {"type": "string"}, "backendId": {"type": "string"}},
                    "additionalProperties": False,
                },
                "WorkspaceConfigureParams": {
                    "type": "object",
                    "required": ["workspaceId", "options"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "options": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
                "DocumentOpenParams": {
                    "type": "object",
                    "required": ["workspaceId", "uri", "languageId", "text"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "uri": {"type": "string"},
                        "languageId": {"type": "string"},
                        "text": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "DocumentChangeParams": {
                    "type": "object",
                    "required": ["workspaceId", "documentId", "text"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "documentId": {"type": "string"},
                        "text": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "DocumentSaveParams": {
                    "type": "object",
                    "required": ["workspaceId", "documentId"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "documentId": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "DocumentCloseParams": {
                    "type": "object",
                    "required": ["workspaceId", "documentId"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "documentId": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "BuildRunParams": {
                    "type": "object",
                    "required": ["workspaceId", "target"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "target": _target_ref_schema(),
                        "budget": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
                "BuildCancelParams": {
                    "type": "object",
                    "required": ["workspaceId"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "ArtifactExportParams": {
                    "type": "object",
                    "required": ["workspaceId", "artifactId"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "artifactId": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "ArtifactReadParams": {
                    "type": "object",
                    "required": ["workspaceId", "artifactId"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "artifactId": {"type": "string"},
                        "maxBytes": {"type": "integer", "minimum": 1},
                    },
                    "additionalProperties": False,
                },
                "QueryParams": {
                    "type": "object",
                    "required": ["workspaceId", "target"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "target": _target_ref_schema(),
                    },
                    "additionalProperties": False,
                },
                "ProbeRunParams": {
                    "type": "object",
                    "required": ["workspaceId", "target", "kind"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "target": _target_ref_schema(),
                        "kind": {"type": "string"},
                        "backend": {"type": "object", "additionalProperties": True},
                        "implementation": {"type": "object", "additionalProperties": True},
                        "options": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
                "ProbeCancelParams": {
                    "type": "object",
                    "required": ["probeRunId"],
                    "properties": {"probeRunId": {"type": "string"}},
                    "additionalProperties": False,
                },
                "ProbeResultsParams": {
                    "type": "object",
                    "required": ["probeRunId"],
                    "properties": {"probeRunId": {"type": "string"}},
                    "additionalProperties": False,
                },
                "AuditRunParams": {
                    "type": "object",
                    "required": ["workspaceId", "target", "include"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "target": _target_ref_schema(),
                        "include": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                    },
                    "additionalProperties": False,
                },
                "AuditSignalsParams": {
                    "type": "object",
                    "required": ["workspaceId", "target"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "target": _target_ref_schema(),
                    },
                    "additionalProperties": False,
                },
                "EventSubscribeParams": {
                    "type": "object",
                    "required": ["topic"],
                    "properties": {"topic": {"type": "string"}},
                    "additionalProperties": False,
                },
                "EventUnsubscribeParams": {
                    "type": "object",
                    "required": ["subscriptionId"],
                    "properties": {"subscriptionId": {"type": "string"}},
                    "additionalProperties": False,
                },
            },
        },
        "results.schema.json": {
            "$schema": SCHEMA_URI,
            "title": "FWP Result Schemas",
            "type": "object",
            "$defs": {
                "AckResult": {
                    "type": "object",
                    "required": ["ok"],
                    "properties": {"ok": {"type": "boolean"}},
                    "additionalProperties": False,
                },
                "ShutdownResult": {
                    "type": "object",
                    "required": ["shutdown"],
                    "properties": {"shutdown": {"type": "boolean"}},
                    "additionalProperties": False,
                },
                "ExitResult": {
                    "type": "object",
                    "required": ["exit"],
                    "properties": {"exit": {"type": "boolean"}},
                    "additionalProperties": False,
                },
                "PingResult": {
                    "type": "object",
                    "required": ["pong", "protocolVersion"],
                    "properties": {
                        "pong": {"type": "boolean"},
                        "protocolVersion": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "BackendCapabilitiesResult": {
                    "type": "object",
                    "required": ["backendId", "capabilities"],
                    "properties": {
                        "backendId": {"type": "string"},
                        "capabilities": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
                "WorkspaceConfigureResult": {
                    "type": "object",
                    "required": ["workspaceId", "configured", "options"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "configured": {"type": "boolean"},
                        "options": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
                "WorkspaceCloseResult": {
                    "type": "object",
                    "required": ["workspaceId", "closed"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "closed": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
                "DocumentCloseResult": {
                    "type": "object",
                    "required": ["documentId", "closed"],
                    "properties": {
                        "documentId": {"type": "string"},
                        "closed": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
                "TargetListResult": {
                    "type": "array",
                    "items": _target_ref_schema(),
                },
                "BuildCancelResult": {
                    "type": "object",
                    "required": ["cancelled", "reason"],
                    "properties": {
                        "cancelled": {"type": "boolean"},
                        "reason": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "ArtifactListResult": {
                    "type": "array",
                    "items": _artifact_ref_schema(),
                },
                "GoalState": {
                    "type": "object",
                    "required": ["goalId", "summary", "facts"],
                    "properties": {
                        "goalId": {"type": "string"},
                        "summary": {"type": "string"},
                        "facts": {"type": "array", "items": {"type": "string"}},
                    },
                    "additionalProperties": True,
                },
                "Diagnostic": {
                    "type": "object",
                    "required": ["severity", "message", "uri"],
                    "properties": {
                        "severity": {"type": "string"},
                        "message": {"type": "string"},
                        "uri": {"type": "string"},
                    },
                    "additionalProperties": True,
                },
                "DependencySlice": {
                    "type": "object",
                    "required": ["target", "dependencies"],
                    "properties": {
                        "target": {"type": "string"},
                        "dependencies": {"type": "array", "items": {"type": "string"}},
                    },
                    "additionalProperties": False,
                },
                "BuildRunResult": {
                    "type": "object",
                    "required": ["status", "artifacts", "rawPayload"],
                    "properties": {
                        "status": {"type": "string"},
                        "artifacts": {"type": "array", "items": _artifact_ref_schema()},
                        "rawPayload": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
                "ArtifactExportResult": {
                    "type": "object",
                    "required": ["artifactId", "exportUri", "kind"],
                    "properties": {
                        "artifactId": {"type": "string"},
                        "exportUri": {"type": "string"},
                        "kind": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "ArtifactReadResult": {
                    "type": "object",
                    "required": ["artifactId", "content", "truncated"],
                    "properties": {
                        "artifactId": {"type": "string"},
                        "content": {"type": "string"},
                        "truncated": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
                "QueryGoalsResult": {
                    "type": "object",
                    "required": ["goals"],
                    "properties": {
                        "goals": {"type": "array", "items": {"type": "object", "required": ["goalId", "summary", "facts"], "properties": {"goalId": {"type": "string"}, "summary": {"type": "string"}, "facts": {"type": "array", "items": {"type": "string"}}}, "additionalProperties": True}},
                    },
                    "additionalProperties": False,
                },
                "QueryDiagnosticsResult": {
                    "type": "object",
                    "required": ["diagnostics"],
                    "properties": {
                        "diagnostics": {"type": "array", "items": {"type": "object", "required": ["severity", "message", "uri"], "properties": {"severity": {"type": "string"}, "message": {"type": "string"}, "uri": {"type": "string"}}, "additionalProperties": True}},
                    },
                    "additionalProperties": False,
                },
                "QueryHoverResult": {
                    "type": "object",
                    "required": ["contents"],
                    "properties": {"contents": {"type": "string"}},
                    "additionalProperties": False,
                },
                "QueryDefinitionResult": {
                    "type": "object",
                    "required": ["symbol", "definition"],
                    "properties": {
                        "symbol": {"type": "string"},
                        "definition": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "QueryTypeResult": {
                    "type": "object",
                    "required": ["symbol", "type"],
                    "properties": {
                        "symbol": {"type": "string"},
                        "type": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "QueryStatusResult": {
                    "type": "object",
                    "required": ["target", "status"],
                    "properties": {
                        "target": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "ProbeRunResult": {
                    "type": "object",
                    "required": ["probeRunId", "kind", "status", "summary", "normalizedResult", "rawPayload"],
                    "properties": {
                        "probeRunId": {"type": "string"},
                        "kind": {"type": "string"},
                        "status": {"type": "string"},
                        "summary": {"type": "string"},
                        "normalizedResult": {"type": "object", "additionalProperties": True},
                        "rawPayload": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
                "ProbeCancelResult": {
                    "type": "object",
                    "required": ["probeRunId", "cancelled"],
                    "properties": {
                        "probeRunId": {"type": "string"},
                        "cancelled": {"type": "boolean"},
                    },
                    "additionalProperties": False,
                },
                "ProbeResultsResult": {
                    "type": "object",
                    "required": ["probeRunId", "results"],
                    "properties": {
                        "probeRunId": {"type": "string"},
                        "results": {"type": "array", "items": {"type": "object", "additionalProperties": True}},
                    },
                    "additionalProperties": False,
                },
                "AuditSignalBundle": {
                    "type": "object",
                    "required": ["workspaceId", "target", "signals", "contractPackRef", "rawPayload"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "target": _target_ref_schema(),
                        "signals": {"type": "array", "items": _signal_schema()},
                        "contractPackRef": {"type": "string"},
                        "rawPayload": {"type": "object", "additionalProperties": True},
                    },
                    "additionalProperties": False,
                },
                "AuditSignalsResult": {
                    "type": "array",
                    "items": _signal_schema(),
                },
                "AuditProfileResult": {
                    "type": "object",
                    "required": ["status", "signalCount", "contractPackRef"],
                    "properties": {
                        "status": {"type": "string"},
                        "signalCount": {"type": "integer", "minimum": 0},
                        "contractPackRef": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "AuditContractPackResult": {
                    "type": "object",
                    "required": ["contractPackRef"],
                    "properties": {"contractPackRef": {"type": "string"}},
                    "additionalProperties": False,
                },
                "EventSubscribeResult": {
                    "type": "object",
                    "required": ["subscriptionId", "topic"],
                    "properties": {
                        "subscriptionId": {"type": "string"},
                        "topic": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "EventUnsubscribeResult": {
                    "type": "object",
                    "required": ["subscriptionId", "unsubscribed", "topic"],
                    "properties": {
                        "subscriptionId": {"type": "string"},
                        "unsubscribed": {"type": "boolean"},
                        "topic": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "ProtocolError": {
                    "type": "object",
                    "required": ["code", "message", "retryable"],
                    "properties": {
                        "code": {"type": "string"},
                        "message": {"type": "string"},
                        "retryable": {"type": "boolean"},
                        "backendKind": {"type": "string"},
                        "correlationId": {"type": "string"},
                    },
                    "additionalProperties": True,
                },
            },
        },
        "events.schema.json": {
            "$schema": SCHEMA_URI,
            "title": "FWP Event Schemas",
            "type": "object",
            "$defs": {
                "BuildUpdateParams": {
                    "type": "object",
                    "required": ["workspaceId", "status", "progress"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "status": {"type": "string"},
                        "progress": {"type": "integer", "minimum": 0},
                    },
                    "additionalProperties": False,
                },
                "GoalsUpdateParams": {
                    "type": "object",
                    "required": ["workspaceId", "goals"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "goals": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["goalId", "summary", "facts"],
                                "properties": {
                                    "goalId": {"type": "string"},
                                    "summary": {"type": "string"},
                                    "facts": {"type": "array", "items": {"type": "string"}},
                                },
                                "additionalProperties": True,
                            },
                        },
                    },
                    "additionalProperties": False,
                },
                "DiagnosticsUpdateParams": {
                    "type": "object",
                    "required": ["workspaceId", "diagnostics"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "diagnostics": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["severity", "message", "uri"],
                                "properties": {
                                    "severity": {"type": "string"},
                                    "message": {"type": "string"},
                                    "uri": {"type": "string"},
                                },
                                "additionalProperties": True,
                            },
                        },
                    },
                    "additionalProperties": False,
                },
                "ProbeUpdateParams": {
                    "type": "object",
                    "required": ["workspaceId", "probeRunId", "status"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "probeRunId": {"type": "string"},
                        "status": {"type": "string"},
                    },
                    "additionalProperties": False,
                },
                "AuditUpdateParams": {
                    "type": "object",
                    "required": ["workspaceId", "signals"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "signals": {"type": "array", "items": _signal_schema()},
                    },
                    "additionalProperties": False,
                },
            },
        },
        "descriptor.schema.json": {
            "$schema": SCHEMA_URI,
            "title": "FWP Descriptor Schema",
            "type": "object",
            "$defs": {
                "Descriptor": {
                    "type": "object",
                    "required": [
                        "name",
                        "version",
                        "protocolVersion",
                        "backendKind",
                        "languages",
                        "capabilities",
                        "transport",
                    ],
                    "properties": {
                        "name": {"type": "string"},
                        "version": {"type": "string"},
                        "protocolVersion": {"type": "string"},
                        "backendKind": {"type": "string"},
                        "languages": {"type": "array", "items": {"type": "string"}, "minItems": 1},
                        "capabilities": {"type": "object", "additionalProperties": True},
                        "transport": {"type": "object", "additionalProperties": True},
                        "argv": {"type": "array", "items": {"type": "string"}},
                        "endpoint": {"type": "string"},
                    },
                    "additionalProperties": False,
                }
            },
        },
        "run-governance.schema.json": {
            "$schema": SCHEMA_URI,
            "title": "FWP Run Governance Schemas",
            "type": "object",
            "$defs": {
                "RunBudget": {
                    **_run_budget_schema(),
                },
                "RunStartParams": {
                    "type": "object",
                    "required": ["workspaceId", "backendId", "kind", "target", "budget"],
                    "properties": {
                        "workspaceId": {"type": "string"},
                        "backendId": {"type": "string"},
                        "kind": {"type": "string"},
                        "target": _target_ref_schema(),
                        "budget": _run_budget_schema(),
                    },
                    "additionalProperties": False,
                },
                "RunPollParams": {
                    "type": "object",
                    "required": ["runId"],
                    "properties": {"runId": {"type": "string"}},
                    "additionalProperties": False,
                },
                "RunStatus": {
                    "type": "object",
                    "required": [
                        "runId",
                        "backend",
                        "kind",
                        "status",
                        "timestamps",
                        "budget",
                        "progress",
                        "signals",
                        "artifactRefs",
                    ],
                    "properties": {
                        "runId": {"type": "string"},
                        "backend": {"type": "string"},
                        "kind": {"type": "string"},
                        "status": {"type": "string"},
                        "timestamps": {"type": "object", "additionalProperties": True},
                        "budget": _run_budget_schema(),
                        "progress": {"type": "object", "additionalProperties": True},
                        "signals": {"type": "array", "items": _signal_schema()},
                        "artifactRefs": {"type": "array", "items": _artifact_ref_schema()},
                    },
                    "additionalProperties": False,
                },
                "RunLogsResult": {
                    "type": "object",
                    "required": ["runId", "logs"],
                    "properties": {
                        "runId": {"type": "string"},
                        "logs": {"type": "array", "items": {"type": "string"}},
                    },
                    "additionalProperties": False,
                },
                "RunArtifactsResult": {
                    "type": "object",
                    "required": ["runId", "artifacts"],
                    "properties": {
                        "runId": {"type": "string"},
                        "artifacts": {"type": "array", "items": _artifact_ref_schema()},
                    },
                    "additionalProperties": False,
                },
            },
        },
    }


def _descriptor(name: str, kind: str) -> dict[str, Any]:
    return {
        "name": name,
        "version": "0.1.0",
        "protocolVersion": PROTOCOL_VERSION,
        "backendKind": kind,
        "languages": [kind],
            "capabilities": backend_capabilities(kind),
        "transport": {"kind": "stdio"},
        "argv": ["python", "-m", f"{kind}_adapter"],
    }


def _transcripts() -> dict[str, dict[str, Any]]:
    budget = {
        "wall_ms": 5000,
        "idle_ms": 1000,
        "cancel_grace_ms": 500,
        "max_rss_mb": 512,
        "max_output_bytes": 16384,
        "max_diag_count": 128,
        "max_children": 2,
        "max_restarts": 0,
    }
    short_budget = dict(budget)
    short_budget["wall_ms"] = 1000
    target = {"kind": "theorem", "ref": "Main.demo"}
    long_target = {"kind": "theorem", "ref": "Main.long"}
    idle_target = {"kind": "theorem", "ref": "Main.stall"}
    no_progress_target = {"kind": "theorem", "ref": "Main.noprogress"}
    stubborn_target = {"kind": "theorem", "ref": "Main.stubborn"}
    return {
        "01-initialize-isabelle": {
            "name": "initialize-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": PROTOCOL_VERSION, "clientInfo": {"name": "fixture-client", "version": "0.1.0"}, "capabilities": {"subscriptions": True, "rawPayload": True}}}},
                {"kind": "response", "forMethod": "initialize", "message": {"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": PROTOCOL_VERSION, "serverInfo": {"name": "formal-hub", "version": "0.1.0"}, "capabilities": backend_capabilities("isabelle")}}},
            ],
        },
        "02-workspace-open-isabelle": {
            "name": "workspace-open-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 2, "method": "workspace/open", "params": {"rootUri": "file:///demo", "backendId": "isabelle-local"}}},
                {"kind": "response", "forMethod": "workspace/open", "message": {"jsonrpc": "2.0", "id": 2, "result": {"workspaceId": "ws_demo", "rootUri": "file:///demo", "backendId": "isabelle-local", "connectionSource": "descriptor", "openedAt": "2026-03-21T00:00:00Z"}}},
            ],
        },
        "03-document-open-isabelle": {
            "name": "document-open-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 3, "method": "document/open", "params": {"workspaceId": "ws_demo", "uri": "file:///demo/Main.thy", "languageId": "isabelle", "text": "theory Main imports Main begin theorem demo: True by simp end"}}},
                {"kind": "response", "forMethod": "document/open", "message": {"jsonrpc": "2.0", "id": 3, "result": {"documentId": "doc_main_thy", "workspaceId": "ws_demo", "uri": "file:///demo/Main.thy", "languageId": "isabelle", "version": 1, "syncMode": "incremental"}}},
            ],
        },
        "04-build-isabelle": {
            "name": "build-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 4, "method": "build/run", "params": {"workspaceId": "ws_demo", "target": target, "budget": budget}}},
                {"kind": "notification", "message": {"jsonrpc": "2.0", "method": "build/update", "params": {"workspaceId": "ws_demo", "status": "running", "progress": 50}}},
                {"kind": "response", "forMethod": "build/run", "message": {"jsonrpc": "2.0", "id": 4, "result": {"status": "ok", "artifacts": [{"artifactId": "artifact_build_log", "kind": "build-log", "uri": "artifact://build/log"}], "rawPayload": {"backend": "isabelle", "tool": "build"}}}},
            ],
        },
        "05-query-goals-isabelle": {
            "name": "query-goals-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 5, "method": "query/goals", "params": {"workspaceId": "ws_demo", "target": target}}},
                {"kind": "notification", "message": {"jsonrpc": "2.0", "method": "goals/update", "params": {"workspaceId": "ws_demo", "goals": [{"goalId": "goal_1", "summary": "1. True", "facts": ["simp"]}]}}},
                {"kind": "response", "forMethod": "query/goals", "message": {"jsonrpc": "2.0", "id": 5, "result": {"goals": [{"goalId": "goal_1", "summary": "1. True", "facts": ["simp"]}]}}},
            ],
        },
        "06-query-diagnostics-lean": {
            "name": "query-diagnostics-lean",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 6, "method": "query/diagnostics", "params": {"workspaceId": "ws_lean", "target": {"kind": "document", "ref": "Main.lean"}}}},
                {"kind": "notification", "message": {"jsonrpc": "2.0", "method": "diagnostics/update", "params": {"workspaceId": "ws_lean", "diagnostics": [{"severity": "warning", "message": "contains admit", "uri": "file:///demo/Main.lean"}]}}},
                {"kind": "response", "forMethod": "query/diagnostics", "message": {"jsonrpc": "2.0", "id": 6, "result": {"diagnostics": [{"severity": "warning", "message": "contains admit", "uri": "file:///demo/Main.lean"}]}}},
            ],
        },
        "07-probe-counterexample-isabelle": {
            "name": "probe-counterexample-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 7, "method": "probe/run", "params": {"workspaceId": "ws_demo", "target": target, "kind": "counterexample", "backend": {"kind": "isabelle"}, "implementation": {"tool": "nitpick"}, "options": {"timeoutMs": 8000}}}},
                {"kind": "notification", "message": {"jsonrpc": "2.0", "method": "probe/update", "params": {"workspaceId": "ws_demo", "probeRunId": "probe_1", "status": "completed"}}},
                {"kind": "response", "forMethod": "probe/run", "message": {"jsonrpc": "2.0", "id": 7, "result": {"probeRunId": "probe_1", "kind": "counterexample", "status": "completed", "summary": "No counterexample found", "normalizedResult": {"outcome": "none"}, "rawPayload": {"tool": "nitpick"}}}},
            ],
        },
        "08-probe-proof-search-isabelle": {
            "name": "probe-proof-search-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 8, "method": "probe/run", "params": {"workspaceId": "ws_demo", "target": target, "kind": "proofSearch", "backend": {"kind": "isabelle"}, "implementation": {"tool": "sledgehammer"}, "options": {"timeoutMs": 5000}}}},
                {"kind": "notification", "message": {"jsonrpc": "2.0", "method": "probe/update", "params": {"workspaceId": "ws_demo", "probeRunId": "probe_2", "status": "completed"}}},
                {"kind": "response", "forMethod": "probe/run", "message": {"jsonrpc": "2.0", "id": 8, "result": {"probeRunId": "probe_2", "kind": "proofSearch", "status": "completed", "summary": "Found candidate proof", "normalizedResult": {"outcome": "candidate", "steps": ["simp"]}, "rawPayload": {"tool": "sledgehammer"}}}},
            ],
        },
        "09-audit-isabelle": {
            "name": "audit-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 9, "method": "audit/run", "params": {"workspaceId": "ws_demo", "target": target, "include": ["trustFrontier", "dependencySlice", "contractPack"]}}},
                {"kind": "notification", "message": {"jsonrpc": "2.0", "method": "audit/update", "params": {"workspaceId": "ws_demo", "signals": [{"kind": "trustFrontier", "status": "trusted"}]}}},
                {"kind": "response", "forMethod": "audit/run", "message": {"jsonrpc": "2.0", "id": 9, "result": {"workspaceId": "ws_demo", "target": target, "signals": [{"kind": "trustFrontier", "status": "trusted"}], "contractPackRef": "contract-pack://main-demo", "rawPayload": {"backend": "isabelle"}}}},
            ],
        },
        "10-artifact-read-isabelle": {
            "name": "artifact-read-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 10, "method": "artifact/read", "params": {"workspaceId": "ws_demo", "artifactId": "artifact_build_log", "maxBytes": 2048}}},
                {"kind": "response", "forMethod": "artifact/read", "message": {"jsonrpc": "2.0", "id": 10, "result": {"artifactId": "artifact_build_log", "content": "Build succeeded", "truncated": False}}},
            ],
        },
        "11-run-timeout-isabelle": {
            "name": "run-timeout-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 11, "method": "run.start", "params": {"workspaceId": "ws_demo", "backendId": "isabelle-local", "kind": "build", "target": target, "budget": short_budget}}},
                {"kind": "response", "forMethod": "run.start", "message": {"jsonrpc": "2.0", "id": 11, "result": {"runId": "run_timeout", "backend": "isabelle", "kind": "build", "status": "timeout.wall", "timestamps": {"startedAt": "2026-03-21T00:00:00Z", "endedAt": "2026-03-21T00:00:01Z"}, "budget": short_budget, "progress": {"percent": 100, "message": "wall timeout"}, "signals": [{"kind": "timeout.wall"}], "artifactRefs": []}}}
            ],
        },
        "12-run-cancel-lean": {
            "name": "run-cancel-lean",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 12, "method": "run.start", "params": {"workspaceId": "ws_lean", "backendId": "lean-local", "kind": "search", "target": long_target, "budget": budget}}},
                {"kind": "response", "forMethod": "run.start", "message": {"jsonrpc": "2.0", "id": 12, "result": {"runId": "run_lean", "backend": "lean", "kind": "search", "status": "running", "timestamps": {"startedAt": "2026-03-21T00:00:00Z"}, "budget": budget, "progress": {"percent": 5, "message": "run created"}, "signals": [], "artifactRefs": []}}},
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 13, "method": "run.cancel", "params": {"runId": "run_lean"}}},
                {"kind": "response", "forMethod": "run.cancel", "message": {"jsonrpc": "2.0", "id": 13, "result": {"runId": "run_lean", "backend": "lean", "kind": "search", "status": "aborted.user_requested", "timestamps": {"startedAt": "2026-03-21T00:00:00Z", "endedAt": "2026-03-21T00:00:01Z"}, "budget": budget, "progress": {"percent": 100, "message": "cancelled"}, "signals": [{"kind": "abort.user_requested"}], "artifactRefs": []}}}
            ],
        },
        "13-run-kill-rocq": {
            "name": "run-kill-rocq",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 14, "method": "run.start", "params": {"workspaceId": "ws_rocq", "backendId": "rocq-local", "kind": "probe", "target": long_target, "budget": budget}}},
                {"kind": "response", "forMethod": "run.start", "message": {"jsonrpc": "2.0", "id": 14, "result": {"runId": "run_rocq", "backend": "rocq", "kind": "probe", "status": "running", "timestamps": {"startedAt": "2026-03-21T00:00:00Z"}, "budget": budget, "progress": {"percent": 5, "message": "run created"}, "signals": [], "artifactRefs": []}}},
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 15, "method": "run.kill", "params": {"runId": "run_rocq"}}},
                {"kind": "response", "forMethod": "run.kill", "message": {"jsonrpc": "2.0", "id": 15, "result": {"runId": "run_rocq", "backend": "rocq", "kind": "probe", "status": "killed", "timestamps": {"startedAt": "2026-03-21T00:00:00Z", "endedAt": "2026-03-21T00:00:02Z"}, "budget": budget, "progress": {"percent": 100, "message": "killed"}, "signals": [{"kind": "resource.child_process_exceeded"}], "artifactRefs": [{"artifactId": "run_rocq_postmortem", "kind": "postmortem", "uri": "artifact://runs/run_rocq/postmortem"}]}}}
            ],
        },
        "14-run-artifacts-isabelle": {
            "name": "run-artifacts-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 14, "method": "run.artifacts", "params": {"runId": "run_done"}}},
                {"kind": "response", "forMethod": "run.artifacts", "message": {"jsonrpc": "2.0", "id": 14, "result": {"runId": "run_done", "artifacts": [{"artifactId": "artifact_postmortem", "kind": "postmortem", "uri": "artifact://postmortem"}]}}}
            ],
        },
        "15-run-idle-timeout-lean": {
            "name": "run-idle-timeout-lean",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 16, "method": "run.start", "params": {"workspaceId": "ws_lean", "backendId": "lean-local", "kind": "search", "target": idle_target, "budget": budget}}},
                {"kind": "response", "forMethod": "run.start", "message": {"jsonrpc": "2.0", "id": 16, "result": {"runId": "run_idle", "backend": "lean", "kind": "search", "status": "running", "timestamps": {"startedAt": "2026-03-21T00:00:00Z"}, "budget": budget, "progress": {"percent": 5, "message": "run created"}, "signals": [], "artifactRefs": []}}},
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 17, "method": "run.poll", "params": {"runId": "run_idle"}}},
                {"kind": "response", "forMethod": "run.poll", "message": {"jsonrpc": "2.0", "id": 17, "result": {"runId": "run_idle", "backend": "lean", "kind": "search", "status": "timeout.idle", "timestamps": {"startedAt": "2026-03-21T00:00:00Z", "endedAt": "2026-03-21T00:00:03Z"}, "budget": budget, "progress": {"percent": 100, "message": "idle timeout"}, "signals": [{"kind": "timeout.idle"}], "artifactRefs": []}}}
            ],
        },
        "16-run-no-progress-isabelle": {
            "name": "run-no-progress-isabelle",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 18, "method": "run.start", "params": {"workspaceId": "ws_demo", "backendId": "isabelle-local", "kind": "search", "target": no_progress_target, "budget": budget}}},
                {"kind": "response", "forMethod": "run.start", "message": {"jsonrpc": "2.0", "id": 18, "result": {"runId": "run_noprogress", "backend": "isabelle", "kind": "search", "status": "running", "timestamps": {"startedAt": "2026-03-21T00:00:00Z"}, "budget": budget, "progress": {"percent": 5, "message": "run created"}, "signals": [], "artifactRefs": []}}},
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 19, "method": "run.poll", "params": {"runId": "run_noprogress"}}},
                {"kind": "response", "forMethod": "run.poll", "message": {"jsonrpc": "2.0", "id": 19, "result": {"runId": "run_noprogress", "backend": "isabelle", "kind": "search", "status": "divergence.no_progress", "timestamps": {"startedAt": "2026-03-21T00:00:00Z", "endedAt": "2026-03-21T00:00:04Z"}, "budget": budget, "progress": {"percent": 100, "message": "repeated non-progress"}, "signals": [{"kind": "divergence.no_progress"}], "artifactRefs": []}}}
            ],
        },
        "17-run-cancel-escalate-kill-lean": {
            "name": "run-cancel-escalate-kill-lean",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 20, "method": "run.start", "params": {"workspaceId": "ws_lean", "backendId": "lean-local", "kind": "search", "target": stubborn_target, "budget": budget}}},
                {"kind": "response", "forMethod": "run.start", "message": {"jsonrpc": "2.0", "id": 20, "result": {"runId": "run_stubborn", "backend": "lean", "kind": "search", "status": "running", "timestamps": {"startedAt": "2026-03-21T00:00:00Z"}, "budget": budget, "progress": {"percent": 5, "message": "run created"}, "signals": [], "artifactRefs": []}}},
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 21, "method": "run.cancel", "params": {"runId": "run_stubborn"}}},
                {"kind": "response", "forMethod": "run.cancel", "message": {"jsonrpc": "2.0", "id": 21, "result": {"runId": "run_stubborn", "backend": "lean", "kind": "search", "status": "running", "timestamps": {"startedAt": "2026-03-21T00:00:00Z"}, "budget": budget, "progress": {"percent": 5, "message": "cancel grace exceeded; kill required"}, "signals": [{"kind": "abort.escalation_pending"}], "artifactRefs": []}}},
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 22, "method": "run.kill", "params": {"runId": "run_stubborn"}}},
                {"kind": "response", "forMethod": "run.kill", "message": {"jsonrpc": "2.0", "id": 22, "result": {"runId": "run_stubborn", "backend": "lean", "kind": "search", "status": "killed", "timestamps": {"startedAt": "2026-03-21T00:00:00Z", "endedAt": "2026-03-21T00:00:06Z"}, "budget": budget, "progress": {"percent": 100, "message": "killed"}, "signals": [{"kind": "resource.child_process_exceeded"}], "artifactRefs": [{"artifactId": "run_stubborn_postmortem", "kind": "postmortem", "uri": "artifact://runs/run_stubborn/postmortem"}]}}}
            ],
        },
        "18-run-logs-after-kill-lean": {
            "name": "run-logs-after-kill-lean",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 23, "method": "run.logs", "params": {"runId": "run_stubborn"}}},
                {"kind": "response", "forMethod": "run.logs", "message": {"jsonrpc": "2.0", "id": 23, "result": {"runId": "run_stubborn", "logs": ["run run_stubborn created", "cooperative cancel timed out; escalation required", "killed", "run killed after escalation"]}}}
            ],
        },
        "19-run-artifacts-after-kill-lean": {
            "name": "run-artifacts-after-kill-lean",
            "steps": [
                {"kind": "request", "message": {"jsonrpc": "2.0", "id": 24, "method": "run.artifacts", "params": {"runId": "run_stubborn"}}},
                {"kind": "response", "forMethod": "run.artifacts", "message": {"jsonrpc": "2.0", "id": 24, "result": {"runId": "run_stubborn", "artifacts": [{"artifactId": "run_stubborn_postmortem", "kind": "postmortem", "uri": "artifact://runs/run_stubborn/postmortem"}]}}}
            ],
        },
    }


def _descriptor_files() -> dict[str, dict[str, Any]]:
    return {
        "isabelle-local.json": _descriptor("isabelle-local", "isabelle"),
        "lean-local.json": _descriptor("lean-local", "lean"),
        "rocq-local.json": _descriptor("rocq-local", "rocq"),
    }


def _schema_fixtures() -> dict[str, Any]:
    return {
        "backendDescriptor": {
            "backendId": "isabelle-local",
            "kind": "isabelle",
            "displayName": "Isabelle",
            "version": "0.1.0",
            "protocolVersion": PROTOCOL_VERSION,
            "languages": ["isabelle"],
            "capabilities": backend_capabilities("isabelle"),
            "transport": {"kind": "stdio"},
            "argv": ["python", "-m", "isabelle_adapter"],
        },
        "workspaceHandle": {
            "workspaceId": "ws_demo",
            "rootUri": "file:///demo",
            "backendId": "isabelle-local",
            "connectionSource": "descriptor",
            "openedAt": "2026-03-21T00:00:00Z",
        },
        "documentHandle": {
            "documentId": "doc_main_thy",
            "workspaceId": "ws_demo",
            "uri": "file:///demo/Main.thy",
            "languageId": "isabelle",
            "version": 1,
            "syncMode": "incremental",
        },
        "targetRef": {"kind": "theorem", "ref": "Main.demo", "workspaceId": "ws_demo"},
        "snapshotRef": {"snapshotId": "snap_doc_main_thy_1", "workspaceId": "ws_demo", "documentId": "doc_main_thy", "backendOpaqueRef": "isabelle:snap_doc_main_thy_1"},
        "goalState": {"goalId": "goal_1", "summary": "1. True", "facts": ["simp"]},
        "diagnostic": {"severity": "warning", "message": "contains sorry", "uri": "file:///demo/Main.thy"},
        "dependencySlice": {"target": "Main.demo", "dependencies": ["Main", "simp"]},
        "protocolError": {"code": "CapabilityError", "message": "unsupported probe", "retryable": False, "backendKind": "lean", "correlationId": "req-1"},
        "buildUpdate": {"workspaceId": "ws_demo", "status": "running", "progress": 50},
        "goalsUpdate": {"workspaceId": "ws_demo", "goals": [{"goalId": "goal_1", "summary": "1. True", "facts": ["simp"]}]},
        "diagnosticsUpdate": {"workspaceId": "ws_demo", "diagnostics": [{"severity": "warning", "message": "contains sorry", "uri": "file:///demo/Main.thy"}]},
        "probeUpdate": {"workspaceId": "ws_demo", "probeRunId": "probe_isabelle_proofSearch", "status": "completed"},
        "auditUpdate": {"workspaceId": "ws_demo", "signals": [{"kind": "trustFrontier", "status": "trusted"}]},
    }


def _capability_matrix() -> dict[str, Any]:
    return {
        "protocolVersion": PROTOCOL_VERSION,
        "backends": {
            "isabelle": backend_capabilities("isabelle"),
            "lean": backend_capabilities("lean"),
            "rocq": backend_capabilities("rocq"),
        },
    }


def _capability_table_markdown() -> str:
    lines = [
        "# Capability Matrix",
        "",
        "| Capability | Isabelle | Lean | Rocq |",
        "|---|---|---|---|",
        f"| Counterexample | yes | no | no |",
        f"| Proof Search | yes | yes | yes |",
        f"| Type Query | yes | yes | no |",
        f"| Trust Frontier | yes | no | no |",
        f"| Run Kill | yes | yes | yes |",
        "",
    ]
    return "\n".join(lines)


def _ui_fixture_manifest() -> dict[str, Any]:
    return {
        "fixtures": [
            {"id": "isabelle-main", "title": "Isabelle Main", "backend": "isabelle", "transcript": "../../../packages/formal-protocol/examples/transcripts/05-query-goals-isabelle.json"},
            {"id": "lean-main", "title": "Lean Main", "backend": "lean", "transcript": "../../../packages/formal-protocol/examples/transcripts/06-query-diagnostics-lean.json"},
            {"id": "rocq-run", "title": "Rocq Run", "backend": "rocq", "transcript": "../../../packages/formal-protocol/examples/transcripts/13-run-kill-rocq.json"},
        ]
    }


def _stack_positioning() -> dict[str, Any]:
    return {
        "layerOrder": ["proof-assistant", "FWP", "formal-claim", "IDE-or-product-shell"],
        "repoPosition": "FWP",
        "owns": [
            "backend-neutral proof protocol",
            "job submission, polling, cancel, and kill semantics",
            "workspace, session, artifact, and export contracts",
            "transport to local or remote proof hosts",
        ],
        "doesNotOwn": [
            "claim graphs",
            "assurance profiles",
            "promotion semantics",
            "product shell UX",
            "proof-host toolchain lifecycle at product scale",
        ],
        "allowedDependencies": {
            "upstreamClients": ["formal-claim"],
            "downstreamHosts": ["proof-assistant"],
            "bridges": ["MCP"],
        },
        "referenceSurfaces": {
            "packages/fwp-client": "canonical upper seam package for formal-claim style callers",
            "apps/ide-shell": "reference client and fixture harness only",
            "integrations/*-adapter": "reference adapter implementations for protocol validation",
            "services/isabelle-runner": "development proof-host shim, not the canonical production proof-assistant owner",
        },
    }


def generate_assets(check: bool = False) -> None:
    outputs: list[tuple[Path, str]] = []
    for name, schema in schema_documents().items():
        outputs.append((_schemas_dir() / name, json.dumps(schema, indent=2) + "\n"))
    for name, descriptor in _descriptor_files().items():
        text = json.dumps(descriptor, indent=2) + "\n"
        outputs.append((_examples_dir() / "descriptors" / name, text))
        outputs.append((_workspace_dir() / ".fwp" / "servers" / name, text))
    for name, transcript in _transcripts().items():
        outputs.append((_examples_dir() / "transcripts" / f"{name}.json", json.dumps(transcript, indent=2) + "\n"))
    outputs.append((_examples_dir() / "capability-matrix.json", json.dumps(_capability_matrix(), indent=2) + "\n"))
    outputs.append((_examples_dir() / "ui-fixtures.json", json.dumps(_ui_fixture_manifest(), indent=2) + "\n"))
    outputs.append((_examples_dir() / "schema-fixtures.json", json.dumps(_schema_fixtures(), indent=2) + "\n"))
    outputs.append((_examples_dir() / "stack-positioning.json", json.dumps(_stack_positioning(), indent=2) + "\n"))
    outputs.append((_docs_dir() / "FWP-08-02-capability-matrix.md", _capability_table_markdown() + "\n"))

    for path, content in outputs:
        path.parent.mkdir(parents=True, exist_ok=True)
        if check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                raise SystemExit(f"Generated asset out of date: {path}")
        else:
            path.write_text(content, encoding="utf-8")
