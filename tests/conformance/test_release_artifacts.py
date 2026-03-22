from __future__ import annotations

import json
import unittest

from scripts.dev.path_setup import activate, repo_root

activate()

from scripts.release.build_release_artifacts import main as build_release_artifacts


class ReleaseArtifactsConformanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()

    def test_release_pack_contains_required_components_and_evidence(self) -> None:
        build_release_artifacts()
        dist = self.root / "dist"
        manifest = json.loads((dist / "release-manifest.json").read_text(encoding="utf-8"))
        evidence = json.loads((dist / "release-evidence.json").read_text(encoding="utf-8"))
        coverage = json.loads((dist / "milestone-coverage.json").read_text(encoding="utf-8"))
        notes = (dist / "release-notes.md").read_text(encoding="utf-8")

        stable = {item["component"] for item in manifest["artifacts"] if item["support"] == "stable"}
        beta = {item["component"] for item in manifest["artifacts"] if item["support"] == "beta"}
        kinds = {item["component"]: item["kind"] for item in manifest["artifacts"]}
        layer_roles = {item["component"]: item["layerRole"] for item in manifest["artifacts"]}

        self.assertTrue({"formal-protocol", "fwp-client", "fwp-mcp-bridge"} <= stable)
        self.assertTrue({"formal-hub", "isabelle-adapter", "lean-adapter", "rocq-adapter", "ide-shell"} <= beta)
        self.assertIn("Support Levels", notes)
        self.assertIn("Stack positioning", notes)
        self.assertIn("Proof client seam", notes)
        self.assertIn("Robustness evidence", notes)
        self.assertIn("Milestone coverage", notes)
        self.assertEqual(kinds["fwp-client"], "client-sdk")
        self.assertEqual(layer_roles["fwp-client"], "FWP-client")
        self.assertEqual(kinds["formal-hub"], "reference-service")
        self.assertEqual(kinds["ide-shell"], "reference-client")
        self.assertEqual(kinds["isabelle-adapter"], "reference-adapter")
        self.assertEqual(layer_roles["formal-protocol"], "FWP-core")
        self.assertEqual(layer_roles["formal-hub"], "FWP-reference-proof-host")
        self.assertEqual(layer_roles["ide-shell"], "FWP-reference-client")
        self.assertEqual(coverage["stepCount"], 60)
        for relative_path in evidence.values():
            self.assertTrue((self.root / relative_path).exists(), relative_path)


if __name__ == "__main__":
    unittest.main()
