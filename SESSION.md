# SESSION.md

## Current milestone
**M0** — Import base, rename, upstream tests green

## Current branch
`chore/scaffold-skeleton`

## PR
Not yet opened — awaiting verification pass then push.

## Last completed step
Commit 4: `tests/conftest.py` + `tests/test_import.py` (smoke tests for all sub-packages).

## Next step
1. Verify `ruff check .`, `ruff format --check .`, and `pytest` all pass.
2. Push `chore/scaffold-skeleton` and open PR into `main`.
3. Wait for user to merge.
4. After merge: start `chore/import-base-engine` — copy `drajb/whisper-local` source into the repo,
   rename package references to `kural`, record upstream commit SHA in `THIRD_PARTY_NOTICES.md`,
   and confirm `pytest` still passes.

## Open questions
- None blocking M0.

## Verify items (from AGENTS.md)
- [ ] **Hotkey-driven only?** AGENTS.md says "Neither appears to offer hands-free activation …
      Both are hotkey-driven (verify)." Confirm in both source repos before M5 planning.
- [ ] **Feature overlap between base and donor** — AGENTS.md says "some features may overlap …
      (verify before porting anything)." Check before port/control-engine starts.

## Decisions recorded (this session)
- Package manager: `uv` + `pyproject.toml` (hatchling backend). Reason: matches system uv
  available on dev machine; avoids setup.py legacy.
- Linter: `ruff` only. Reason: handles pycodestyle + isort + pyupgrade in one tool.
- Sub-package layout: `engine/`, `control/`, `config/`, `ui/` as top-level siblings under `kural/`.
  Reason: clean separation of concerns; each milestone targets exactly one sub-package.
- pytest markers defined: `gpu`, `mic`, `slow`. Reason: CI can deselect hardware-dependent
  tests with `-m 'not gpu and not mic'`.
