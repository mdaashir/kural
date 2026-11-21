# Memory — PyPI publisher uv setup fix

Last updated: 2026-11-21

## What was built
On `fix/pypi-publisher-uv-setup`, the isolated publish job now installs uv 0.13.9 (matching build.yml) and Python 3.12 before running uvx. A ruamel.yaml workflow regression test verifies ordering and matching pins. README, RELEASE, CHANGELOG and SESSION document the failure and pending publication.

## Decisions made
Keep cmd-kural version 0.1.2 and all existing tags unchanged. A pending Trusted Publisher can create the project on first successful upload; it does not reserve the name. No pre-existing project claim is required. Runtime import and CLI remain `kural`; the unrelated PyPI `kural` project must not be used.

## Problems solved
Approved publisher run `44851392430` failed metadata validation with `uvx: command not found`, exit 127. Tools installed in reusable build jobs are not available in the separate publish job.

## Current state
GitHub Release v0.1.2 exists. PyPI cmd-kural 0.1.2 JSON endpoint still returns 404; publication remains pending. Local Ruff check/format pass and 584 pytest tests pass. actionlint is unavailable on PATH. Fix PR is to be opened after commit/push; find it by the branch above.

## Next session starts with
Review the fix PR and actual CI results. After owner merge, use a separately authorized fresh dispatch from main targeting existing v0.1.2, rather than rerunning the failed workflow definition. This task does not merge, dispatch publication, approve deployments, or change tags.

## Open questions
OIDC and the first upload remain unverified. No desktop rebuild or live GPU/microphone/UI test was needed for this workflow-only fix. Existing v0.1.1 is also immutable and must not be moved.
