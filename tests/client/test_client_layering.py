from __future__ import annotations

import ast
import unittest

from scripts.dev.path_setup import activate, repo_root

activate()


class ProofClientLayeringTest(unittest.TestCase):
    def test_client_seam_does_not_import_hub_or_backend_modules(self) -> None:
        root = repo_root()
        client_module = root / "packages" / "fwp-client" / "src" / "fwp_client" / "client.py"
        tree = ast.parse(client_module.read_text(encoding="utf-8"))

        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name.split(".")[0])
            if isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_modules.add(node.module.split(".")[0])

        self.assertIn("formal_protocol", imported_modules)
        self.assertFalse({"formal_hub", "isabelle_adapter", "lean_adapter", "rocq_adapter"} & imported_modules)

    def test_client_readme_marks_upper_layer_boundary(self) -> None:
        root = repo_root()
        readme = (root / "packages" / "fwp-client" / "README.md").read_text(encoding="utf-8")
        self.assertIn("upper dependency point", readme)
        self.assertIn("formal-claim", readme)
        self.assertIn("does not own claim, assurance, or promotion semantics", readme)


if __name__ == "__main__":
    unittest.main()
