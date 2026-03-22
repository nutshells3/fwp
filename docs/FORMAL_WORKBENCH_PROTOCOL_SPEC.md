# Formal Workbench Protocol (FWP) — Standalone Planning Specification

## 1. Purpose

Formal Workbench Protocol (FWP) is a standalone upper-layer protocol for integrating multiple proof assistants and formal systems into one workbench, IDE shell, audit pipeline, and agent runtime.

The protocol is not intended to replace backend-native protocols such as Isabelle server / PIDE, Lean LSP, or Rocq LSP / Petanque. It sits above them and provides one normalized control surface for:

- workspace discovery
- document/session lifecycle
- build and artifact access
- theorem/query access
- backend probes (counterexample, proof search, replay, perturbation)
- audit signal extraction
- contract-pack emission for claim / assurance workflows

FWP exists to solve the N×M integration problem inside the formal tooling stack:

- N backends: Isabelle, Lean, Rocq, later Dafny, Why3, HOL4, ACL2, etc.
- M clients: IDE shell, CLI, MCP host, planner, auditor, batch runner, CI

Without FWP, every client must implement every backend adapter separately.

## 2. Design Position

### 2.1 What FWP is

FWP is a universal formal-workbench protocol.

It standardizes the *upper-layer operations* that an editor, runner, auditor, or agent host needs from a formal backend.

### 2.2 What FWP is not

FWP is **not**:

- a universal proof kernel
- a universal proof term language
- a replacement for PIDE, LSP, SerAPI, Rocq LSP, Lake, or backend-native build tools
- a mandate that all proof assistants expose the same low-level command granularity
- a requirement that all normalized results erase backend-specific detail

## 3. Core Principles

### 3.1 Capability-first

Every backend advertises capabilities. Clients discover support instead of assuming it.

Examples:

- `documentSync`
- `workspaceDiscovery`
- `buildTargets`
- `goalQueries`
- `dependencies`
- `counterexampleProbe`
- `proofSearchProbe`
- `auditSignals`
- `contractPack`
- `rawPayload`
- `subscriptions`

### 3.2 Adapter architecture

FWP requires backend adapters.

The IDE or agent host talks only to the FWP hub. The hub talks to backend adapters. Each adapter translates between FWP and the backend-native protocol.

### 3.3 Normalized model + raw payload

Every response may contain:

- normalized FWP fields for cross-backend UX and policy logic
- raw backend payload for lossless debugging, backend-specific UI, and future reprocessing

### 3.4 Backend escape hatch

FWP intentionally reserves backend namespaces:

- `backend/isabelle/*`
- `backend/lean/*`
- `backend/rocq/*`

The common layer must remain minimal and stable. Rich backend-specific features live behind namespaced extensions.

### 3.5 Transport neutrality, JSON-RPC wire format

FWP uses JSON-RPC 2.0. Local transport defaults to stdio. Remote/shared workers may use streamable HTTP.

### 3.6 Discovery over hard-coded configuration

A workspace can contain one or more backend connection descriptors. Clients discover available backends instead of assuming them.

### 3.7 No premature renaming of current domain APIs

Existing project-level functions such as `run_nitpick_probe` do not need to be renamed before the current backlog finishes.

FWP generalizes them later by mapping them into a backend-agnostic request shape, e.g.:

- `kind = "counterexample"`
- `backend.kind = "isabelle"`
- `implementation.tool = "nitpick"`

## 4. Protocol Goals

FWP v1 must support the following:

1. Open and manage a formal workspace.
2. Discover available backend adapters in that workspace.
3. Open/change/save/close documents incrementally where the backend supports it.
4. Run builds for sessions/modules/packages/targets.
5. Query goals, diagnostics, definitions, types, dependencies, and artifacts.
6. Run proof-related probes and surface their results in a normalized shape.
7. Emit audit signals and contract packs to the assurance core.
8. Expose a narrow MCP bridge for LLM/agent use without making MCP the core runtime protocol.

## 5. Non-goals for v1

FWP v1 explicitly does **not** attempt to do the following:

- unify proof terms across assistants
- unify tactic ASTs
- unify every semantic notion of context, state, obligation, universe, section, locale, module, or namespace
- provide a complete backend-independent theorem export language
- model every interactive widget protocol in Lean or every backend-specific PIDE markup stream in Isabelle
- hide performance and trust differences between backends

## 6. Architectural Layers

### 6.1 Layer A — Native backend protocol

Examples:

- Isabelle server / PIDE-related services and `build/export/dump`
- Lean language server and Lake
- Rocq LSP, Petanque, and `fcc`

### 6.2 Layer B — FWP adapter

Each adapter is responsible for:

- process startup and shutdown
- workspace/session bootstrap
- message translation
- backend capability discovery
- normalized result construction
- raw payload preservation
- error normalization
- provenance tagging

### 6.3 Layer C — FWP hub

The hub is a single broker that:

- manages adapter registry
- routes requests to the right adapter
- aggregates subscriptions
- stores session/workspace state
- enforces protocol contracts
- emits normalized events to IDE/CLI/MCP bridge clients

### 6.4 Layer D — Clients

Clients include:

- standalone IDE shell
- CLI
- CI runner
- assurance core
- MCP bridge
- future batch agents

## 7. Protocol Entities

### 7.1 BackendDescriptor

Describes an installed or discoverable backend adapter.

Fields:

- `backendId`
- `kind`
- `displayName`
- `version`
- `protocolVersion`
- `languages`
- `capabilities`
- `transport`
- `argv` or remote endpoint descriptor

### 7.2 WorkspaceHandle

Represents a workspace root plus a chosen adapter instance.

Fields:

- `workspaceId`
- `rootUri`
- `backendId`
- `connectionSource`
- `openedAt`

### 7.3 DocumentHandle

Represents an opened source document.

Fields:

- `documentId`
- `workspaceId`
- `uri`
- `languageId`
- `version`
- `syncMode`

### 7.4 TargetRef

References a build/query target.

Possible forms:

- session
- theory/module/file
- package
- theorem declaration
- object-level goal reference

### 7.5 SnapshotRef

Represents a backend-known snapshot or document/session state.

Fields:

- `snapshotId`
- `workspaceId`
- `documentId?`
- `backendOpaqueRef?`

### 7.6 ProbeRun

Represents an invocation of a proof-related probe.

Fields:

- `probeRunId`
- `kind`
- `backend`
- `implementation`
- `target`
- `status`
- `summary`
- `normalizedResult`
- `rawPayload`

### 7.7 AuditSignalBundle

Represents backend-extracted or synthesized audit signals such as:

- trust frontier
- oracle/axiom/admitted dependency
- counterexample results
- replay success/failure
- perturbation outcomes
- theorem-local dependency slices
- export/dump provenance

## 8. Method Families

## 8.1 Lifecycle

- `initialize`
- `initialized`
- `shutdown`
- `exit`
- `ping`

`initialize` performs version negotiation, client/server identification, and capability exchange.

## 8.2 Discovery

- `backend/list`
- `backend/discover`
- `backend/capabilities`
- `backend/describe`

## 8.3 Workspace management

- `workspace/open`
- `workspace/configure`
- `workspace/close`

## 8.4 Document management

- `document/open`
- `document/change`
- `document/save`
- `document/close`

The adapter may internally translate these into incremental document operations, batch file writes, or temporary workspace materialization.

## 8.5 Build and artifacts

- `target/list`
- `build/run`
- `build/cancel`
- `artifact/list`
- `artifact/read`
- `artifact/export`

## 8.6 Queries

- `query/goals`
- `query/hover`
- `query/definition`
- `query/type`
- `query/dependencies`
- `query/diagnostics`
- `query/status`

## 8.7 Probes

- `probe/run`
- `probe/cancel`
- `probe/results`

Probe kinds in v1:

- `counterexample`
- `proofSearch`
- `replay`
- `premiseDeletion`
- `conclusionPerturbation`
- `consistencyCheck`
- `dependencySlice`
- `buildReplay`

## 8.8 Audit

- `audit/run`
- `audit/signals`
- `audit/profile`
- `audit/contractPack`

## 8.9 Backend escape hatch

- `backend/isabelle/*`
- `backend/lean/*`
- `backend/rocq/*`

## 9. Event Model

FWP supports subscriptions and notifications.

Core notifications:

- `progress/update`
- `diagnostics/update`
- `goals/update`
- `build/update`
- `artifact/produced`
- `probe/update`
- `audit/update`
- `log/message`

Notifications are best-effort and capability-gated.

## 10. Capability Model

Capabilities are declared during `initialize`.

Example server capability object:

```json
{
  "protocolVersion": "2026-03-20",
  "capabilities": {
    "workspaceDiscovery": true,
    "documentSync": {
      "mode": "incremental"
    },
    "buildTargets": true,
    "queries": {
      "goals": true,
      "hover": true,
      "definition": true,
      "type": true,
      "dependencies": true,
      "diagnostics": true
    },
    "probes": {
      "counterexample": true,
      "proofSearch": true,
      "replay": true,
      "premiseDeletion": true,
      "conclusionPerturbation": true,
      "consistencyCheck": false
    },
    "auditSignals": {
      "trustFrontier": true,
      "rawBackendPayload": true
    },
    "subscriptions": {
      "progress": true,
      "diagnostics": true,
      "goals": false
    },
    "experimental": {
      "backend/isabelle/exportPatterns": true
    }
  }
}
```

## 11. Discovery File

FWP should adopt a BSP-like discovery model.

Suggested workspace file:

- `.fwp/servers/<name>.json`

Example:

```json
{
  "name": "isabelle-local",
  "version": "1.0.0",
  "protocolVersion": "2026-03-20",
  "backendKind": "isabelle",
  "languages": ["isabelle"],
  "capabilities": {
    "workspaceDiscovery": true,
    "buildTargets": true,
    "auditSignals": true
  },
  "transport": {
    "kind": "stdio"
  },
  "argv": [
    "python",
    "-m",
    "formal_claim_isabelle_adapter"
  ]
}
```

Rules:

1. multiple descriptors may coexist in one workspace
2. descriptors may be version-controlled if they do not contain machine-local secrets or absolute paths
3. the hub may merge workspace-level and user-level descriptors
4. a single workspace may expose multiple backends simultaneously

## 12. Normalized Data Shapes

FWP must define JSON schemas for at least the following:

- `InitializeParams`
- `InitializeResult`
- `BackendDescriptor`
- `WorkspaceOpenParams`
- `DocumentChangeParams`
- `BuildRunParams`
- `GoalState`
- `Diagnostic`
- `DependencySlice`
- `ProbeRunRequest`
- `ProbeRunResult`
- `AuditRunRequest`
- `AuditSignalBundle`
- `ContractPackRef`
- `ProtocolError`

All schemas should use JSON Schema 2020-12.

## 13. Example Requests

### 13.1 Initialize

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2026-03-20",
    "clientInfo": {
      "name": "proof-claim-formal-hub",
      "version": "0.1.0"
    },
    "capabilities": {
      "subscriptions": true,
      "rawPayload": true,
      "experimental": {}
    }
  }
}
```

### 13.2 Run a backend-neutral counterexample probe

```json
{
  "jsonrpc": "2.0",
  "id": 15,
  "method": "probe/run",
  "params": {
    "workspaceId": "ws_01",
    "target": {
      "kind": "theorem",
      "ref": "Main.dispatch_driver_assignment_converges"
    },
    "kind": "counterexample",
    "backend": {
      "kind": "isabelle"
    },
    "implementation": {
      "tool": "nitpick"
    },
    "options": {
      "timeoutMs": 8000
    }
  }
}
```

### 13.3 Request an audit bundle

```json
{
  "jsonrpc": "2.0",
  "id": 21,
  "method": "audit/run",
  "params": {
    "workspaceId": "ws_01",
    "target": {
      "kind": "theorem",
      "ref": "Main.dispatch_driver_assignment_converges"
    },
    "include": [
      "trustFrontier",
      "dependencySlice",
      "probeSummaries",
      "contractPack"
    ]
  }
}
```

## 14. Error Model

FWP needs a protocol-level error taxonomy.

Recommended top-level classes:

- `ProtocolError`
- `CapabilityError`
- `TransportError`
- `WorkspaceError`
- `DocumentError`
- `BuildError`
- `ProbeError`
- `AuditError`
- `BackendInternalError`

Each error should include:

- stable error code
- human-readable message
- retryability
- backend kind
- raw backend diagnostics if available
- correlation id / request id

## 15. Security Model

### 15.1 Baseline

FWP should adopt a conservative security posture:

- stdio is the default local transport
- remote transport must be explicit
- no implicit filesystem or shell access beyond adapter declaration
- no secret-bearing connection descriptors in VCS
- protocol logs must support redaction
- raw payload passthrough must be bounded and tagged

### 15.2 Trust boundaries

There are three trust boundaries:

1. client ↔ hub
2. hub ↔ adapter
3. adapter ↔ native backend

### 15.3 Backend execution policy

Adapters must declare:

- executable paths
- sandbox expectations
- writable directories
- network policy
- temp workspace policy

## 16. Versioning and Extensions

FWP should use date-based protocol versions, e.g. `2026-03-20`.

Rules:

- no silent breaking changes
- additive features gated by capabilities
- backend-specific extensions go into namespaced capability keys and method spaces
- deprecated fields remain until at least one later date-stamped protocol release

## 17. Relationship to MCP

FWP is not a replacement for MCP.

FWP should expose an MCP bridge with a small, safe subset of operations:

- discover backends
- open workspace
- run selected probes
- read selected artifacts
- request an audit bundle
- read contract-pack references

The MCP bridge should not expose arbitrary backend-native operations by default.

## 18. Relationship to Existing Project State

This protocol project starts **after** the current assurance-core backlog is completed.

Until then:

- keep existing backend-specific runner methods if they serve the current milestones
- avoid premature renaming churn
- insert protocol seams only where it reduces future migration cost without destabilizing M4–M9 work

## 19. Recommended Repository Layout

```text
packages/
  formal-protocol/
    schemas/
    examples/
    golden-transcripts/
  formal-normalized-models/

services/
  formal-hub/
  fwp-mcp-bridge/

integrations/
  isabelle-adapter/
  lean-adapter/
  rocq-adapter/

apps/
  ide-shell/

tests/
  protocol/
  transcripts/
  adapters/
```

## 20. Delivery Strategy

### Phase 0 — Precondition

Finish the current product backlog first.

### Phase 1 — Protocol contract only

- write schemas
- write examples
- define capability model
- define discovery descriptors
- define golden transcripts

### Phase 2 — Single-backend hub

- implement `formal-hub`
- connect Isabelle adapter only
- do not change existing assurance logic beyond adapter boundaries

### Phase 3 — MCP bridge

- expose a narrow agent-facing subset
- verify prompt/tool safety and bounded execution

### Phase 4 — New backends

- Lean adapter
- Rocq adapter

### Phase 5 — IDE shell

- connect one editor shell to FWP
- goals, diagnostics, builds, probes, audits

## 21. Acceptance Criteria for v1

FWP v1 is acceptable when all of the following hold:

1. a client can discover at least one backend from a workspace descriptor
2. the hub can initialize and negotiate capabilities
3. Isabelle can be driven through the adapter without exposing backend-native commands directly to the client
4. `probe/run(kind="counterexample")` works end-to-end through Isabelle with backend-tagged implementation detail
5. the hub can emit a normalized audit bundle and preserve raw backend payload
6. the MCP bridge can safely expose a restricted subset to LLM hosts
7. a second backend can be added without changing the core client protocol

## 22. Risks

### 22.1 Over-generalization risk

Trying to unify command spans, proof states, or tactic models too early will stall the project.

Mitigation: standardize only upper-layer operations.

### 22.2 Lowest-common-denominator risk

If normalization erases too much backend detail, the protocol becomes useless.

Mitigation: normalized + raw dual payload.

### 22.3 Premature multi-backend refactor

Starting this before the current backlog is complete will destabilize the assurance core.

Mitigation: defer protocol implementation until the current milestones close.

### 22.4 Security drift

A protocol that reaches into local provers and filesystems can become an unsafe remote-execution substrate.

Mitigation: stdio-first, explicit descriptors, redacted logs, bounded raw payload, capability gating.

## 23. Decision Summary

Build FWP as an upper-layer workbench protocol, not as a universal low-level proof assistant protocol.

Keep the current project backlog intact.

After the current backlog completes:

1. define the protocol contracts
2. build the hub
3. wrap Isabelle first
4. add MCP bridge
5. add Lean and Rocq adapters
6. integrate one IDE shell
