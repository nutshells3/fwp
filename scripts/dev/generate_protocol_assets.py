from __future__ import annotations

import argparse

from path_setup import activate


def main() -> int:
    activate()
    from formal_protocol.assets import generate_assets

    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    generate_assets(check=args.check)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
