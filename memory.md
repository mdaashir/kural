# Memory — GHCR Docker Containerization

Last updated: 2026-11-21

## Current state
- `cmd-kural==0.1.3` is published on PyPI via Trusted Publishing (OIDC); verified via `uv tool install "cmd-kural[runtime,tray]==0.1.3"`.
- GitHub Release `v0.1.3` is live with all 5 assets verified against `SHA256SUMS`.
- Working branch: `feat/ghcr-docker-container`. Implemented headless Whisper API containerization (`Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.github/workflows/docker.yml`, and `tests/test_docker.py`).
- Next milestone: Modernized Next.js marketing and documentation site deployed to GitHub Pages.

## Decisions
- Headless API container image targets `ghcr.io/mdaashir/kural` so GitHub automatically surfaces it in the repository's Packages column.
- Non-root user `kural` (UID 10001), healthcheck via `curl` on `/health`, pinned uv `0.13.9`.
- By default, `docker-compose.yml` binds port `7777` strictly to host loopback (`127.0.0.1:7777`) to protect the unauthenticated transcription API.
- Added `server` dependency extra in `pyproject.toml` so container builds install only server-required packages.

## Verification
- `ruff check .` and `ruff format --check .` passed (143 files).
- `pytest -q`: 589 passed (includes 4 tests in `tests/test_docker.py`).
- `uv lock --check` and `uv sync --dry-run --locked --extra dev` passed.
- `git diff --check` passed cleanly.
