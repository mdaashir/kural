# SESSION.md

## Current milestone
**Headless Whisper API Containerization & GitHub Container Registry (GHCR)**

## Current branch
`feat/ghcr-docker-container`

## PR
To be opened via gh after verification passes.

## Last completed step
- `cmd-kural==0.1.3` is live and verified on PyPI; `uv tool install "cmd-kural[runtime,tray]==0.1.3"` verified locally.
- Implemented containerization for Kural's headless Whisper API:
  - Multi-stage Linux `Dockerfile` (`python:3.12-slim`, non-root user `kural`, pinned `uv 0.13.9`, healthcheck, `ffmpeg`).
  - `.dockerignore` excluding `.git`, `.venv`, and temporary artifacts.
  - `docker-compose.yml` binding port `7777` strictly to host loopback `127.0.0.1` for privacy.
  - Added `server` optional dependency extra in `pyproject.toml` (`faster-whisper`, `soxr`, `soundfile`) and updated `uv.lock`.
  - Added GitHub Actions workflow `.github/workflows/docker.yml` building and publishing to `ghcr.io/mdaashir/kural` on tag/push to main, with PR container smoke testing.
  - Added regression test suite `tests/test_docker.py` (4 tests).

## Verification
- `ruff check .` and `ruff format --check .` passed (143 files).
- `pytest -q`: 589 passed.
- `uv lock --check` and `uv sync --dry-run --locked --extra dev` passed.
- `git diff --check` passed cleanly.

## Next steps
1. Commit and push branch `feat/ghcr-docker-container`, open PR into `main`.
2. Wait for user review and merge.
3. Next milestone: Modernized Next.js marketing and documentation site deployed to GitHub Pages.

## Open limitations
- Container image provides headless transcription API only; desktop UI, system tray, hotkeys, and Windows audio capture are not included.
