from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.dev.path_setup import repo_root


def main() -> int:
    root = repo_root()
    subprocess.run([sys.executable, "scripts/dev/check_repo.py", "--mode", "test"], cwd=root, check=True)
    subprocess.run([sys.executable, "scripts/release/build_release_artifacts.py"], cwd=root, check=True)
    for path in ["dist/release-manifest.json", "dist/release-notes.md", "dist/release-evidence.json", "dist/milestone-coverage.json"]:
        if not (root / path).exists():
            raise SystemExit(f"Missing release artifact: {path}")
    print("Release smoke passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
