from __future__ import annotations

from path_setup import activate


def main() -> int:
    activate()
    from formal_protocol.assets import generate_assets

    generate_assets(check=False)
    print("FWP bootstrap complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
