# Memory — cmd-kural installed version fix

Last updated: 2026-11-21

## Current state
Published PyPI `cmd-kural==0.1.2` was installed in an isolated uv tool environment and reproduced stale version output: package metadata 0.1.2, `kural.__version__` 0.1.0, and `kural --version` 0.1.0-dev. Fix branch `fix/cmd-kural-installed-version` now derives installed versions from distribution metadata `cmd-kural`; source checkouts use `0+unknown`, and frozen apps read the bundled `cmd-kural` pyproject version. Package version is prepared as 0.1.3. Published tags/releases v0.1.0, v0.1.1, and v0.1.2 remain unchanged.

## Verification
- `uv lock --check`, locked dev dependency resolution, wheel/sdist build, and strict Twine metadata checks pass.
- Isolated uv tool smoke from both wheel and sdist verifies distribution metadata, module version, utility version, and CLI output `kural 0.1.3`.
- Ruff lint/format pass; pytest: 585 passed.
- PyPI 0.1.3 is not published; no new tag/release was created.

## Decisions and release gates
- Keep distribution name `cmd-kural`; CLI/import name remains `kural`.
- Never mutate published versions/tags. Version correction ships only as 0.1.3.
- Release tag creation requires user review/merge of the fix PR and explicit release authorization.
- PyPI upload additionally requires verified Trusted Publisher, protected GitHub `pypi` environment, `PUBLISH_PYPI=true`, and explicit user authorization/approval. No PyPI publish has run for 0.1.3.

## Next steps
1. Review final diff, commit/push the focused fix PR, and verify hosted CI.
2. Wait for review and merge before any release/tag.
3. After explicit authorization, create annotated v0.1.3 from merged main, verify release artifacts/checksums, then complete PyPI gate/setup and publish only with approval.

## Historical milestones
The project roadmap M0–M5 and subsequent desktop/runtime milestones remain documented in the earlier project history; this note records current package-release status.
