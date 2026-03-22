from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.dev.path_setup import activate, repo_root
from scripts.release.milestone_coverage import milestone_coverage


def _release_manifest(protocol_version: str) -> dict[str, object]:
    return {
        "name": "fwp-v0.1.0",
        "version": "0.1.0",
        "protocolVersion": protocol_version,
        "releaseDate": protocol_version,
        "support": {
            "stable": ["formal-protocol", "fwp-client", "fwp-mcp-bridge"],
            "beta": ["formal-hub", "isabelle-adapter", "lean-adapter", "rocq-adapter", "ide-shell"],
            "experimental": ["backend escape hatch"],
        },
        "artifacts": [
            {"component": "formal-protocol", "path": "packages/formal-protocol/schemas", "kind": "schema-pack", "support": "stable", "layerRole": "FWP-core"},
            {"component": "formal-protocol", "path": "packages/formal-protocol/examples", "kind": "example-pack", "support": "stable", "layerRole": "FWP-core"},
            {"component": "fwp-client", "path": "packages/fwp-client/src", "kind": "client-sdk", "support": "stable", "layerRole": "FWP-client"},
            {"component": "formal-hub", "path": "services/formal-hub/src", "kind": "reference-service", "support": "beta", "layerRole": "FWP-reference-proof-host"},
            {"component": "fwp-mcp-bridge", "path": "services/fwp-mcp-bridge/src", "kind": "service", "support": "stable", "layerRole": "FWP-bridge"},
            {"component": "isabelle-adapter", "path": "integrations/isabelle-adapter/src", "kind": "reference-adapter", "support": "beta", "layerRole": "FWP-reference-proof-host-adapter"},
            {"component": "lean-adapter", "path": "integrations/lean-adapter/src", "kind": "reference-adapter", "support": "beta", "layerRole": "FWP-reference-proof-host-adapter"},
            {"component": "rocq-adapter", "path": "integrations/rocq-adapter/src", "kind": "reference-adapter", "support": "beta", "layerRole": "FWP-reference-proof-host-adapter"},
            {"component": "ide-shell", "path": "apps/ide-shell/src", "kind": "reference-client", "support": "beta", "layerRole": "FWP-reference-client"},
            {"component": "docs", "path": "docs/protocol", "kind": "documentation", "support": "stable", "layerRole": "FWP-governance"},
            {"component": "tests", "path": "tests", "kind": "verification", "support": "stable", "layerRole": "FWP-verification"},
        ],
        "evidence": {
            "stackPositioning": "docs/protocol/FWP-01-05-stack-positioning.md",
            "proofClientSeam": "docs/protocol/FWP-01-06-proof-client-seam.md",
            "referenceManual": "docs/protocol/FWP-08-01-reference-manual.md",
            "implementerGuide": "docs/protocol/FWP-08-01-implementer-guide.md",
            "capabilityMatrix": "docs/protocol/FWP-08-02-capability-matrix.md",
            "robustness": "docs/protocol/FWP-08-03-robustness-evidence.md",
            "httpHardening": "docs/protocol/FWP-08-04-http-transport-hardening.md",
            "releaseBoundary": "docs/protocol/FWP-08-05-v0.1-release.md",
            "milestoneCoverage": "dist/milestone-coverage.json",
            "runGovernance": "docs/protocol/FWP-RG-01-run-governance.md",
            "runFixtures": "docs/protocol/FWP-RG-12-conformance-fixtures.md",
            "operatorDefaults": "docs/protocol/FWP-RG-13-operator-defaults.md",
        },
    }


def _release_notes(manifest: dict[str, object]) -> str:
    support = manifest["support"]
    evidence = manifest["evidence"]
    return "\n".join(
        [
            "# FWP v0.1.0",
            "",
            f"- Protocol version: `{manifest['protocolVersion']}`",
            f"- Release date: `{manifest['releaseDate']}`",
            "",
            "## Support Levels",
            "",
            f"- Stable: {', '.join(support['stable'])}",
            f"- Beta: {', '.join(support['beta'])}",
            f"- Experimental: {', '.join(support['experimental'])}",
            "",
            "Reference-only surfaces remain in the repo for conformance and seam validation.",
            "They are not the canonical production proof-host implementation.",
            "",
            "## Evidence",
            "",
            f"- Stack positioning: `{evidence['stackPositioning']}`",
            f"- Proof client seam: `{evidence['proofClientSeam']}`",
            f"- Reference manual: `{evidence['referenceManual']}`",
            f"- Capability matrix: `{evidence['capabilityMatrix']}`",
            f"- Robustness evidence: `{evidence['robustness']}`",
            f"- HTTP hardening: `{evidence['httpHardening']}`",
            f"- Release boundary: `{evidence['releaseBoundary']}`",
            f"- Milestone coverage: `{evidence['milestoneCoverage']}`",
            f"- Run governance: `{evidence['runGovernance']}`",
            f"- Run fixtures: `{evidence['runFixtures']}`",
            f"- Operator defaults: `{evidence['operatorDefaults']}`",
            "",
        ]
    )


def main() -> int:
    activate()
    from formal_protocol import PROTOCOL_VERSION

    root = repo_root()
    dist = root / "dist"
    dist.mkdir(parents=True, exist_ok=True)
    manifest = _release_manifest(PROTOCOL_VERSION)
    coverage = milestone_coverage(PROTOCOL_VERSION)
    release_notes = _release_notes(manifest)
    (dist / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (dist / "milestone-coverage.json").write_text(json.dumps(coverage, indent=2) + "\n", encoding="utf-8")
    (dist / "release-notes.md").write_text(release_notes, encoding="utf-8")
    (dist / "release-evidence.json").write_text(json.dumps(manifest["evidence"], indent=2) + "\n", encoding="utf-8")
    print("Release manifest and notes written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
