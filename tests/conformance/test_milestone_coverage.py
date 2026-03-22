from __future__ import annotations

import json
import unittest

from scripts.dev.path_setup import activate, repo_root

activate()

from scripts.release.build_release_artifacts import main as build_release_artifacts


class MilestoneCoverageConformanceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()

    def test_release_pack_contains_full_milestone_coverage(self) -> None:
        build_release_artifacts()
        coverage = json.loads((self.root / "dist" / "milestone-coverage.json").read_text(encoding="utf-8"))

        self.assertEqual(coverage["stepCount"], 60)
        self.assertEqual(coverage["status"], "done")
        self.assertEqual(len(coverage["steps"]), 60)
        self.assertEqual(coverage["steps"][0]["id"], "FWP-00-01")
        self.assertEqual(coverage["steps"][-1]["id"], "FWP-RG-13")

        for step in coverage["steps"]:
            self.assertEqual(step["status"], "done")
            self.assertGreaterEqual(len(step["evidence"]), 2)
            for item in step["evidence"]:
                self.assertTrue((self.root / item["path"]).exists(), item["path"])


if __name__ == "__main__":
    unittest.main()
