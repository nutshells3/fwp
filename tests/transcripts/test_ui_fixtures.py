from __future__ import annotations

import json
import unittest

from scripts.dev.path_setup import activate, repo_root

activate()


class UIFixturesTest(unittest.TestCase):
    def test_fixture_manifest_points_to_multiple_backends(self) -> None:
        root = repo_root()
        manifest = json.loads((root / "packages" / "formal-protocol" / "examples" / "ui-fixtures.json").read_text(encoding="utf-8"))
        backends = {fixture["backend"] for fixture in manifest["fixtures"]}
        self.assertGreaterEqual(len(backends), 2)
        notification_count = 0
        for fixture in manifest["fixtures"]:
            transcript = (root / "apps" / "ide-shell" / "src" / fixture["transcript"]).resolve()
            self.assertTrue(transcript.exists(), transcript)
            transcript_data = json.loads(transcript.read_text(encoding="utf-8"))
            notification_count += len([step for step in transcript_data["steps"] if step["kind"] == "notification"])
        self.assertGreaterEqual(notification_count, 2)


if __name__ == "__main__":
    unittest.main()
