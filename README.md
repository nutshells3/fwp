# FWP

FWP is the Formal Workbench Protocol layer: a backend-neutral seam between
upper orchestration systems and lower proof hosts.

This repository is not a claim engine and not a prover host. It exists to
define and exercise the protocol, reference client surface, bridge policies,
contract assets, and conformance workflow that sit between those two layers.

## Role In The Stack

The intended split is:

```text
IDE / product shell
  -> orchestration-assurance-engine
    -> FWP
      -> proof-assistant
        -> Isabelle / Lean / Rocq
```

FWP owns:

- protocol contracts and schema-backed assets
- backend-neutral client API
- reference hub surface
- allowlisted MCP bridge surface
- transcript fixtures and conformance tests

FWP does not own:

- claim semantics
- assurance or promotion policy
- product-shell UX
- actual proof-host execution

Proof execution belongs in `proof-assistant`. Assurance and workflow semantics
belong above this repo.

## What Works Today

- protocol assets and helper library in `packages/formal-protocol`
- backend-neutral reference client in `packages/fwp-client`
- reference hub service in `services/formal-hub`
- allowlisted MCP-facing bridge in `services/fwp-mcp-bridge`
- backend adapter integration packages for Isabelle, Lean, and Rocq
- example workspace and transcript fixtures
- conformance, security, transcript, adapter, and client tests
- release/build asset generation under `dist/`

The current repo is intentionally shaped as a protocol monorepo rather than a
single Python package.

## Repository Layout

```text
apps/
  ide-shell/
examples/
  workspaces/demo/
integrations/
  isabelle-adapter/
  lean-adapter/
  rocq-adapter/
packages/
  formal-protocol/
  fwp-client/
services/
  formal-hub/
  fwp-mcp-bridge/
scripts/
tests/
dist/
```

Important surfaces:

- `packages/formal-protocol/`: schemas, descriptors, examples, transcript assets, validation helpers
- `packages/fwp-client/`: caller-facing client transport and workspace/job/artifact helpers
- `services/formal-hub/`: reference JSON-RPC hub surface
- `services/fwp-mcp-bridge/`: sanitized, allowlisted MCP bridge over the hub
- `integrations/*-adapter/`: backend-specific integration packages
- `examples/workspaces/demo/`: multi-backend demo workspace

## Main Components

### `formal-protocol`

This package holds the machine-readable protocol assets:

- JSON Schemas
- descriptor fixtures
- transcript fixtures
- schema validation helpers
- asset generation helpers

### `fwp-client`

The client package is the main upper-layer dependency point. It currently
supports:

- local in-process hub transport
- remote HTTP hub transport
- workspace bootstrapping from caller inputs
- build/audit submission
- governed job polling, cancel, and kill
- merged artifact access across workspace artifacts and run artifacts

### `formal-hub`

`formal-hub` is the reference protocol broker inside this repo. It manages
workspace state, transcripts, notifications, and routing. In the target stack
it is not the authoritative proof host; that role belongs to `proof-assistant`.

### `fwp-mcp-bridge`

The MCP bridge is intentionally narrow. It allowlists a small set of tools,
schema-validates inputs and outputs, and sanitizes sensitive fields before they
leave the bridge boundary.

## Commands

Bootstrap:

```powershell
python scripts/dev/bootstrap.py
```

Generate/check protocol assets:

```powershell
python scripts/dev/generate_protocol_assets.py
python scripts/dev/check_repo.py --mode lint
```

Run tests:

```powershell
python scripts/dev/check_repo.py --mode test
```

If you prefer `just`:

```powershell
just bootstrap
just generate-assets
just lint
just test
just release-build
just release-smoke
```

## Example Uses

Use the reference hub as a lightweight protocol server:

```powershell
python -m formal_hub.server --http-enable --host 127.0.0.1 --port 8765
```

Use the client package against a hub endpoint or local hub object:

- submit formalization checks
- submit audit probes
- poll governed jobs
- read workspace and run artifacts through one client surface

Use the MCP bridge to expose a sanitized protocol surface to higher-level agent
or tool callers.

## Tests

The test suite spans several layers:

- protocol contract validation
- transcript replay
- hub routing
- client layering
- bridge security
- run-governance behavior
- adapter integration paths
- release/milestone asset checks

Representative tests live under:

- `tests/protocol/`
- `tests/client/`
- `tests/security/`
- `tests/conformance/`
- `tests/adapters/`
- `tests/transcripts/`

## Positioning

FWP is the reusable orchestration seam. If you need a stable boundary between
an assurance/orchestration engine above and proof-host runtimes below, this repo
is that boundary.
