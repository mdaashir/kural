# SESSION.md

## Current milestone
**Release Preparation for v0.1.0 (Documentation, Changelog & Maintainer Runbook)**

## Current branch
`chore/prepare-release-v0.1.0`

## PR
PR to be opened with gh after verification passes.

## Last completed step
PR #94 merged into main (CI run 44766083309 passed all jobs). Prepared repository for initial `v0.1.0` release:
1. Created `CHANGELOG.md` following Keep a Changelog standard detailing all additions across M0 through M5 and post-M5 desktop features.
2. Created `RELEASE.md` maintainer guide documenting the automated release workflow, pre-release checklist, tag creation (`git tag -a v0.1.0`), SHA256 checksum verification, post-release smoke testing, and rollback procedures.
3. Updated `README.md` with links to `CHANGELOG.md` and `RELEASE.md`, and added `anomalyco/hex` to the main README attribution section.
4. Refreshed `memory.md` to reflect `v0.1.0` release preparation readiness.
5. All 579 offline unit tests passing; Ruff lint and format checks passing.

## Next step
1. Commit, push `chore/prepare-release-v0.1.0`, and open a PR with gh.
2. Wait for user review and merge into `main`.
3. After merge, user executes: `git tag -a v0.1.0 -m "Release v0.1.0: Local-first voice typing and voice control for Windows"` and `git push origin v0.1.0` to trigger the automated release workflow.

## Limitations and decisions
- Kept `version = "0.1.0"` in `pyproject.toml` matching target tag `v0.1.0`.
- Release workflow is verified via CI on `main` and dry-run tests; actual GitHub Release creation will occur when the tag is pushed to GitHub.
- PyPI publishing remains opt-in via repository variable `PUBLISH_PYPI == 'true'` and requires PyPI trusted publisher configuration.
