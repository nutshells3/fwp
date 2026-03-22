from __future__ import annotations

from typing import Any


def doc(path: str) -> dict[str, str]:
    return {"kind": "doc", "path": path}


def impl(path: str) -> dict[str, str]:
    return {"kind": "implementation", "path": path}


def test(path: str) -> dict[str, str]:
    return {"kind": "verification", "path": path}


def step(step_id: str, milestone: str, title: str, *evidence: dict[str, str]) -> dict[str, Any]:
    return {
        "id": step_id,
        "milestone": milestone,
        "title": title,
        "status": "done",
        "evidence": list(evidence),
    }


def milestone_coverage(protocol_version: str) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []

    steps.extend(
        [
            step(
                "FWP-00-01",
                "FWP-00",
                "Gate protocol work until current assurance-core backlog is closed",
                doc("docs/protocol/FWP-00-01-post-core-gate.md"),
                doc("docs/protocol/README.md"),
                test("tests/conformance/test_release_artifacts.py"),
            ),
            step(
                "FWP-00-02",
                "FWP-00",
                "Freeze current backend-specific API names until adapter migration phase",
                doc("docs/protocol/FWP-00-02-api-freeze-policy.md"),
                doc("docs/protocol/README.md"),
                test("tests/conformance/test_release_artifacts.py"),
            ),
        ]
    )

    for step_id, title, doc_path in [
        ("FWP-01-01", "Write protocol charter and scope boundaries", "docs/protocol/FWP-01-01-charter-and-scope.md"),
        ("FWP-01-02", "Write protocol glossary and entity model", "docs/protocol/FWP-01-02-glossary-and-entity-model.md"),
        ("FWP-01-03", "Define protocol versioning policy and extension policy", "docs/protocol/FWP-01-03-versioning-and-extension-policy.md"),
        ("FWP-01-04", "Define threat model and trust boundaries for hub, adapters, and remote transports", "docs/protocol/FWP-01-04-threat-model-and-trust-boundaries.md"),
    ]:
        steps.append(step(step_id, "FWP-01", title, doc(doc_path), doc("docs/protocol/README.md"), test("tests/conformance/test_release_artifacts.py")))

    steps.extend(
        [
            step(
                "FWP-02-01",
                "FWP-02",
                "Create packages/formal-protocol package skeleton",
                impl("packages/formal-protocol/pyproject.toml"),
                impl("packages/formal-protocol/README.md"),
                test("tests/protocol/test_protocol_contracts.py"),
            ),
            step(
                "FWP-02-02",
                "FWP-02",
                "Define JSON Schema for initialize and capability negotiation",
                impl("packages/formal-protocol/schemas/initialize.schema.json"),
                impl("packages/formal-protocol/src/formal_protocol/assets.py"),
                test("tests/protocol/test_protocol_contracts.py"),
            ),
            step(
                "FWP-02-03",
                "FWP-02",
                "Define JSON Schema for workspace, document, target, and snapshot objects",
                impl("packages/formal-protocol/schemas/entities.schema.json"),
                impl("packages/formal-protocol/src/formal_protocol/assets.py"),
                test("tests/protocol/test_protocol_contracts.py"),
            ),
            step(
                "FWP-02-04",
                "FWP-02",
                "Define JSON Schema for build, artifact, query, probe, and audit methods",
                impl("packages/formal-protocol/schemas/methods.schema.json"),
                impl("packages/formal-protocol/src/formal_protocol/assets.py"),
                test("tests/protocol/test_protocol_contracts.py"),
            ),
            step(
                "FWP-02-05",
                "FWP-02",
                "Define JSON Schema for normalized result objects and protocol errors",
                impl("packages/formal-protocol/schemas/results.schema.json"),
                impl("packages/formal-protocol/src/formal_protocol/assets.py"),
                test("tests/protocol/test_protocol_contracts.py"),
            ),
            step(
                "FWP-02-06",
                "FWP-02",
                "Define workspace discovery descriptor schema",
                impl("packages/formal-protocol/schemas/descriptor.schema.json"),
                impl("packages/formal-protocol/src/formal_protocol/assets.py"),
                test("tests/protocol/test_protocol_contracts.py"),
            ),
            step(
                "FWP-02-07",
                "FWP-02",
                "Create golden protocol examples and transcripts",
                impl("packages/formal-protocol/examples/transcripts/01-initialize-isabelle.json"),
                impl("packages/formal-protocol/examples/schema-fixtures.json"),
                test("tests/protocol/test_transcript_replay.py"),
            ),
            step(
                "FWP-02-08",
                "FWP-02",
                "Add schema validation and transcript conformance tests to root CI",
                impl("scripts/dev/check_repo.py"),
                impl("packages/formal-protocol/src/formal_protocol/schema_tools.py"),
                test("tests/protocol/test_protocol_contracts.py"),
                test("tests/protocol/test_transcript_replay.py"),
            ),
        ]
    )

    steps.extend(
        [
            step(
                "FWP-03-01",
                "FWP-03",
                "Create services/formal-hub service skeleton",
                impl("services/formal-hub/pyproject.toml"),
                impl("services/formal-hub/src/formal_hub/__init__.py"),
                test("tests/protocol/test_hub_routing.py"),
            ),
            step(
                "FWP-03-02",
                "FWP-03",
                "Implement protocol session manager and request router",
                impl("services/formal-hub/src/formal_hub/hub.py"),
                impl("services/formal-hub/src/formal_hub/server.py"),
                test("tests/protocol/test_hub_routing.py"),
            ),
            step(
                "FWP-03-03",
                "FWP-03",
                "Implement adapter registry and capability cache",
                impl("services/formal-hub/src/formal_hub/hub.py"),
                impl("services/formal-hub/src/formal_hub/adapter.py"),
                test("tests/protocol/test_hub_routing.py"),
            ),
            step(
                "FWP-03-04",
                "FWP-03",
                "Implement event/subscription channel for progress, diagnostics, goals, and audit updates",
                impl("services/formal-hub/src/formal_hub/hub.py"),
                impl("packages/formal-protocol/schemas/events.schema.json"),
                test("tests/protocol/test_transcript_replay.py"),
            ),
            step(
                "FWP-03-05",
                "FWP-03",
                "Implement transcript recorder and replay harness for hub-level tests",
                impl("services/formal-hub/src/formal_hub/transcripts.py"),
                impl("packages/formal-protocol/examples/transcripts/09-audit-isabelle.json"),
                test("tests/protocol/test_transcript_replay.py"),
            ),
            step(
                "FWP-03-06",
                "FWP-03",
                "Add formal backend adapter interface contract in Python",
                impl("services/formal-hub/src/formal_hub/adapter.py"),
                impl("integrations/isabelle-adapter/src/isabelle_adapter/adapter.py"),
                test("tests/adapters/test_isabelle_e2e.py"),
            ),
        ]
    )

    steps.extend(
        [
            step(
                "FWP-04-01",
                "FWP-04",
                "Create integrations/isabelle-adapter package by wrapping services/isabelle-runner",
                impl("integrations/isabelle-adapter/pyproject.toml"),
                impl("integrations/isabelle-adapter/src/isabelle_adapter/adapter.py"),
                impl("integrations/isabelle-adapter/README.md"),
                test("tests/adapters/test_isabelle_e2e.py"),
            ),
            step(
                "FWP-04-02",
                "FWP-04",
                "Map Isabelle workspace/build/export/dump flow onto FWP build and artifact methods",
                impl("integrations/isabelle-adapter/src/isabelle_adapter/adapter.py"),
                impl("services/formal-hub/src/formal_hub/adapter.py"),
                test("tests/adapters/test_isabelle_e2e.py"),
            ),
            step(
                "FWP-04-03",
                "FWP-04",
                "Map theorem-local trust, Nitpick, Sledgehammer, and perturbation probes onto FWP probe methods",
                impl("integrations/isabelle-adapter/src/isabelle_adapter/adapter.py"),
                impl("integrations/isabelle-adapter/README.md"),
                test("tests/adapters/test_isabelle_e2e.py"),
            ),
            step(
                "FWP-04-04",
                "FWP-04",
                "Expose audit bundle and contract-pack emission through Isabelle adapter",
                impl("integrations/isabelle-adapter/src/isabelle_adapter/adapter.py"),
                impl("packages/formal-protocol/examples/transcripts/09-audit-isabelle.json"),
                test("tests/adapters/test_isabelle_e2e.py"),
            ),
            step(
                "FWP-04-05",
                "FWP-04",
                "Add end-to-end hub + Isabelle adapter transcript tests",
                impl("packages/formal-protocol/examples/transcripts/05-query-goals-isabelle.json"),
                test("tests/adapters/test_isabelle_e2e.py"),
                test("tests/protocol/test_transcript_replay.py"),
            ),
        ]
    )

    steps.extend(
        [
            step(
                "FWP-05-01",
                "FWP-05",
                "Create services/fwp-mcp-bridge service skeleton",
                impl("services/fwp-mcp-bridge/pyproject.toml"),
                impl("services/fwp-mcp-bridge/src/fwp_mcp_bridge/bridge.py"),
                test("tests/security/test_bridge_security.py"),
            ),
            step(
                "FWP-05-02",
                "FWP-05",
                "Define bridge policy for which FWP methods may be exposed as MCP tools/resources",
                doc("docs/protocol/FWP-05-02-bridge-policy.md"),
                impl("services/fwp-mcp-bridge/README.md"),
                test("tests/security/test_bridge_security.py"),
            ),
            step(
                "FWP-05-03",
                "FWP-05",
                "Implement MCP tools for backend discovery, workspace open, probe run, artifact read, and audit run",
                impl("services/fwp-mcp-bridge/src/fwp_mcp_bridge/bridge.py"),
                impl("services/fwp-mcp-bridge/README.md"),
                test("tests/security/test_bridge_security.py"),
            ),
            step(
                "FWP-05-04",
                "FWP-05",
                "Implement MCP resources for descriptors, golden transcripts, and selected artifact views",
                impl("services/fwp-mcp-bridge/src/fwp_mcp_bridge/bridge.py"),
                impl("packages/formal-protocol/examples/transcripts/10-artifact-read-isabelle.json"),
                test("tests/security/test_bridge_security.py"),
            ),
            step(
                "FWP-05-05",
                "FWP-05",
                "Add bridge abuse tests for prompt-injection, over-broad file access, and raw payload leakage",
                doc("docs/protocol/FWP-05-02-bridge-policy.md"),
                test("tests/security/test_bridge_security.py"),
                test("tests/security/test_hub_robustness.py"),
            ),
        ]
    )

    steps.extend(
        [
            step(
                "FWP-06-01",
                "FWP-06",
                "Create integrations/lean-adapter package skeleton",
                impl("integrations/lean-adapter/pyproject.toml"),
                impl("integrations/lean-adapter/src/lean_adapter/adapter.py"),
                test("tests/adapters/test_secondary_backend_e2e.py"),
            ),
            step(
                "FWP-06-02",
                "FWP-06",
                "Implement Lean workspace discovery and Lake-aware build mapping",
                impl("integrations/lean-adapter/src/lean_adapter/adapter.py"),
                impl("packages/formal-protocol/examples/descriptors/lean-local.json"),
                test("tests/adapters/test_secondary_backend_e2e.py"),
            ),
            step(
                "FWP-06-03",
                "FWP-06",
                "Implement Lean document/query mapping through the Lean language server",
                impl("integrations/lean-adapter/src/lean_adapter/adapter.py"),
                impl("examples/workspaces/demo/Main.lean"),
                test("tests/adapters/test_secondary_backend_e2e.py"),
            ),
            step(
                "FWP-06-04",
                "FWP-06",
                "Define Lean probe surface and normalized result mapping",
                impl("integrations/lean-adapter/src/lean_adapter/adapter.py"),
                impl("packages/formal-protocol/examples/capability-matrix.json"),
                test("tests/adapters/test_secondary_backend_e2e.py"),
            ),
            step(
                "FWP-06-05",
                "FWP-06",
                "Create integrations/rocq-adapter package skeleton",
                impl("integrations/rocq-adapter/pyproject.toml"),
                impl("integrations/rocq-adapter/src/rocq_adapter/adapter.py"),
                test("tests/adapters/test_secondary_backend_e2e.py"),
            ),
            step(
                "FWP-06-06",
                "FWP-06",
                "Implement Rocq document/query mapping through rocq-lsp",
                impl("integrations/rocq-adapter/src/rocq_adapter/adapter.py"),
                impl("examples/workspaces/demo/Main.v"),
                test("tests/adapters/test_secondary_backend_e2e.py"),
            ),
            step(
                "FWP-06-07",
                "FWP-06",
                "Implement Rocq low-latency probe pathway using petanque/fcc-aware adapter hooks",
                impl("integrations/rocq-adapter/src/rocq_adapter/adapter.py"),
                impl("packages/formal-protocol/examples/capability-matrix.json"),
                test("tests/adapters/test_secondary_backend_e2e.py"),
            ),
            step(
                "FWP-06-08",
                "FWP-06",
                "Add capability matrix and cross-backend compatibility tests for Isabelle, Lean, and Rocq",
                doc("docs/protocol/FWP-08-02-capability-matrix.md"),
                impl("packages/formal-protocol/examples/capability-matrix.json"),
                test("tests/adapters/test_cross_backend.py"),
            ),
        ]
    )

    steps.extend(
        [
            step(
                "FWP-07-01",
                "FWP-07",
                "Create apps/ide-shell protocol driver abstraction",
                impl("apps/ide-shell/src/driver.js"),
                impl("apps/ide-shell/README.md"),
                test("tests/transcripts/test_ui_fixtures.py"),
            ),
            step(
                "FWP-07-02",
                "FWP-07",
                "Implement documents/diagnostics/goals panel against FWP only",
                impl("apps/ide-shell/src/app.js"),
                impl("apps/ide-shell/src/index.html"),
                test("tests/transcripts/test_ui_fixtures.py"),
            ),
            step(
                "FWP-07-03",
                "FWP-07",
                "Implement build/probe/audit panels against FWP only",
                impl("apps/ide-shell/src/app.js"),
                impl("apps/ide-shell/src/driver.js"),
                test("tests/transcripts/test_ui_fixtures.py"),
            ),
            step(
                "FWP-07-04",
                "FWP-07",
                "Add transcript-based UI fixtures for at least two backends",
                impl("packages/formal-protocol/examples/ui-fixtures.json"),
                impl("apps/ide-shell/README.md"),
                test("tests/transcripts/test_ui_fixtures.py"),
            ),
        ]
    )

    steps.extend(
        [
            step(
                "FWP-08-01",
                "FWP-08",
                "Write protocol reference manual and implementer guide",
                doc("docs/protocol/FWP-08-01-reference-manual.md"),
                doc("docs/protocol/FWP-08-01-implementer-guide.md"),
                test("tests/conformance/test_release_artifacts.py"),
            ),
            step(
                "FWP-08-02",
                "FWP-08",
                "Publish machine-readable capability matrix and compatibility table",
                doc("docs/protocol/FWP-08-02-capability-matrix.md"),
                impl("packages/formal-protocol/examples/capability-matrix.json"),
                test("tests/adapters/test_cross_backend.py"),
            ),
            step(
                "FWP-08-03",
                "FWP-08",
                "Add protocol fuzzing and malformed-message robustness tests",
                doc("docs/protocol/FWP-08-03-robustness-evidence.md"),
                impl("services/formal-hub/src/formal_hub/hub.py"),
                test("tests/security/test_hub_robustness.py"),
            ),
            step(
                "FWP-08-04",
                "FWP-08",
                "Add remote transport hardening for streamable HTTP mode",
                doc("docs/protocol/FWP-08-04-http-transport-hardening.md"),
                impl("services/formal-hub/src/formal_hub/server.py"),
                test("tests/security/test_hub_robustness.py"),
            ),
            step(
                "FWP-08-05",
                "FWP-08",
                "Cut FWP v0.1 release with schemas, hub, Isabelle adapter, MCP bridge, and one secondary backend in beta",
                doc("docs/protocol/FWP-08-05-v0.1-release.md"),
                impl("scripts/release/build_release_artifacts.py"),
                test("tests/conformance/test_release_artifacts.py"),
            ),
        ]
    )

    steps.extend(
        [
            step(
                "FWP-RG-01",
                "FWP-RG",
                "Define budgeted run lifecycle methods and terminal states",
                doc("docs/protocol/FWP-RG-01-run-governance.md"),
                impl("packages/formal-protocol/schemas/run-governance.schema.json"),
                test("tests/conformance/test_run_governance.py"),
            ),
            step(
                "FWP-RG-02",
                "FWP-RG",
                "Add RunBudget schema with wall, idle, grace, memory, output, and child-process limits",
                impl("packages/formal-protocol/schemas/run-governance.schema.json"),
                impl("packages/formal-protocol/src/formal_protocol/assets.py"),
                test("tests/protocol/test_protocol_contracts.py"),
            ),
            step(
                "FWP-RG-03",
                "FWP-RG",
                "Add backend-specific budget hint extensions for search-heavy and heartbeat-limited backends",
                impl("packages/formal-protocol/examples/capability-matrix.json"),
                impl("packages/formal-protocol/src/formal_protocol/assets.py"),
                test("tests/protocol/test_protocol_contracts.py"),
            ),
            step(
                "FWP-RG-04",
                "FWP-RG",
                "Define normalized divergence, timeout, resource, and user-abort signals",
                impl("packages/formal-protocol/schemas/run-governance.schema.json"),
                impl("packages/formal-protocol/examples/transcripts/16-run-no-progress-isabelle.json"),
                test("tests/conformance/test_run_governance.py"),
            ),
            step(
                "FWP-RG-05",
                "FWP-RG",
                "Define cooperative-cancel to hard-kill escalation policy",
                doc("docs/protocol/FWP-RG-01-run-governance.md"),
                impl("packages/formal-protocol/src/formal_protocol/assets.py"),
                test("tests/conformance/test_run_governance.py"),
            ),
            step(
                "FWP-RG-06",
                "FWP-RG",
                "Add run-governance capabilities to initialize and backend capability descriptors",
                impl("services/formal-hub/src/formal_hub/hub.py"),
                impl("packages/formal-protocol/examples/capability-matrix.json"),
                test("tests/conformance/test_run_governance.py"),
            ),
            step(
                "FWP-RG-07",
                "FWP-RG",
                "Add normalized run status, progress, and artifact-log access model",
                impl("packages/formal-protocol/schemas/run-governance.schema.json"),
                impl("services/formal-hub/src/formal_hub/hub.py"),
                test("tests/conformance/test_run_governance.py"),
            ),
            step(
                "FWP-RG-08",
                "FWP-RG",
                "Implement hub-side run controller and bounded job registry",
                doc("docs/protocol/FWP-RG-01-run-governance.md"),
                impl("services/formal-hub/src/formal_hub/hub.py"),
                test("tests/conformance/test_run_governance.py"),
            ),
            step(
                "FWP-RG-09",
                "FWP-RG",
                "Map Isabelle adapter build, check, search, and probe execution onto run-governance contract",
                impl("integrations/isabelle-adapter/src/isabelle_adapter/adapter.py"),
                impl("packages/formal-protocol/schemas/run-governance.schema.json"),
                test("tests/conformance/test_run_governance.py"),
            ),
            step(
                "FWP-RG-10",
                "FWP-RG",
                "Map Lean adapter build, check, and search execution onto run-governance contract",
                impl("integrations/lean-adapter/src/lean_adapter/adapter.py"),
                impl("packages/formal-protocol/schemas/run-governance.schema.json"),
                test("tests/adapters/test_secondary_backend_e2e.py"),
            ),
            step(
                "FWP-RG-11",
                "FWP-RG",
                "Expose run-governance methods through MCP bridge without leaking backend ownership",
                impl("services/fwp-mcp-bridge/src/fwp_mcp_bridge/bridge.py"),
                doc("docs/protocol/FWP-05-02-bridge-policy.md"),
                test("tests/security/test_bridge_security.py"),
            ),
            step(
                "FWP-RG-12",
                "FWP-RG",
                "Add conformance fixtures and golden transcripts for timeout, cancel, kill, and post-run artifact access",
                doc("docs/protocol/FWP-RG-12-conformance-fixtures.md"),
                impl("packages/formal-protocol/examples/transcripts/19-run-artifacts-after-kill-lean.json"),
                test("tests/conformance/test_run_governance.py"),
            ),
            step(
                "FWP-RG-13",
                "FWP-RG",
                "Add operator-facing safety defaults, queue limits, and release gates for governed runs",
                doc("docs/protocol/FWP-RG-13-operator-defaults.md"),
                impl("packages/formal-protocol/src/formal_protocol/assets.py"),
                test("tests/conformance/test_run_governance.py"),
            ),
        ]
    )

    if len(steps) != 60:
        raise ValueError(f"Expected 60 milestone rows, found {len(steps)}")

    return {
        "protocolVersion": protocol_version,
        "generatedAt": protocol_version,
        "stepCount": len(steps),
        "status": "done",
        "steps": steps,
    }
