from __future__ import annotations

import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def source_paths() -> list[Path]:
    root = repo_root()
    patterns = [
        "packages/*/src",
        "services/*/src",
        "integrations/*/src",
    ]
    paths: list[Path] = []
    for pattern in patterns:
        paths.extend(sorted(root.glob(pattern)))
    return [path for path in paths if path.is_dir()]


def activate() -> Path:
    root = repo_root()
    for path in source_paths():
        text = str(path)
        if text not in sys.path:
            sys.path.insert(0, text)
    return root
