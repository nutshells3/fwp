from __future__ import annotations

import argparse
import subprocess
import sys

from path_setup import activate, repo_root


def run_tests() -> None:
    root = repo_root()
    subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        cwd=root,
        check=True,
    )


def run_lint() -> None:
    activate()
    from formal_protocol.assets import generate_assets

    generate_assets(check=True)
    print("Asset generation check passed.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["test", "lint"], default="test")
    args = parser.parse_args()
    activate()
    if args.mode == "test":
        run_tests()
    else:
        run_lint()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
