# Memory — OCI Package Linking & Docker Hub Support

Last updated: 2026-11-21

## Current state
- `cmd-kural==0.1.3` is published on PyPI.
- GitHub Release `v0.1.3` is live with all 5 assets verified against `SHA256SUMS`.
- GitHub Pages is live and deployed at **https://mdaashir.github.io/kural/** with active `github-pages` environment deployment.
- Working branch: `chore/package-linking-and-dockerhub`.
  - Added OCI source labels to `Dockerfile` (`org.opencontainers.image.source`) so GitHub links the GHCR container directly to the repository's **Packages** sidebar.
  - Added optional Docker Hub publishing to `.github/workflows/docker.yml` supporting token and secretless OIDC (`DOCKERHUB_OIDC_CONNECTIONID`).
  - Added unit tests in `tests/test_docker.py`.

## Decisions
- OCI source annotation `https://github.com/mdaashir/kural` is the required standard for GitHub to link GHCR images to repository packages.
- Docker Hub publishing is optional and non-blocking: skips gracefully if credentials or OIDC connection ID are not configured.

## Verification
- `ruff check .` and `ruff format --check .` passed.
- `pytest -q`: 590 passed.
- `site/` static export tests: 4 passed.
- `git diff --check` passed cleanly.
