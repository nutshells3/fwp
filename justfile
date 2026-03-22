set shell := ["sh", "-cu"]
set windows-shell := ["powershell", "-NoLogo", "-NoProfile", "-Command"]

default:
  @just --list

bootstrap:
  python scripts/dev/bootstrap.py

generate-assets:
  python scripts/dev/generate_protocol_assets.py

test:
  python scripts/dev/check_repo.py --mode test

lint:
  python scripts/dev/check_repo.py --mode lint

release-build:
  python scripts/release/build_release_artifacts.py

release-smoke:
  python scripts/release/smoke_release.py
