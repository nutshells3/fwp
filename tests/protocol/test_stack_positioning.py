from __future__ import annotations

import json
import unittest

from scripts.dev.path_setup import activate, repo_root

activate()


class StackPositioningTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = repo_root()

    def test_machine_readable_stack_positioning_matches_formal_claim_architecture(self) -> None:
        positioning = json.loads(
            (self.root / "packages" / "formal-protocol" / "examples" / "stack-positioning.json").read_text(encoding="utf-8")
        )
        self.assertEqual(positioning["layerOrder"], ["proof-assistant", "FWP", "formal-claim", "IDE-or-product-shell"])
        self.assertEqual(positioning["repoPosition"], "FWP")
        self.assertIn("claim graphs", positioning["doesNotOwn"])
        self.assertIn("formal-claim", positioning["allowedDependencies"]["upstreamClients"])
        self.assertIn("proof-assistant", positioning["allowedDependencies"]["downstreamHosts"])
        self.assertEqual(positioning["referenceSurfaces"]["packages/fwp-client"], "canonical upper seam package for formal-claim style callers")
        self.assertEqual(positioning["referenceSurfaces"]["apps/ide-shell"], "reference client and fixture harness only")

    def test_stack_positioning_doc_exists_and_mentions_reference_surfaces(self) -> None:
        doc = (self.root / "docs" / "protocol" / "FWP-01-05-stack-positioning.md").read_text(encoding="utf-8")
        self.assertIn("Frozen Layer Order", doc)
        self.assertIn("packages/fwp-client", doc)
        self.assertIn("apps/ide-shell", doc)
        self.assertIn("proof-assistant", doc)
        self.assertIn("formal-claim", doc)


if __name__ == "__main__":
    unittest.main()
