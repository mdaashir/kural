# SESSION.md

## Current milestone
**Fix CI & Release Dependency Resolution**

## Current branch
`fix/ci-dependency-resolution`

## PR
PR to be opened with gh after verification passes.

## Last completed step
PR #91 merged into main. In GitHub Actions run 44741897768, `uv sync --extra dev` failed because `kural[runtime]` specified `global-hotkeys>=0.6.0`, but only `global-hotkeys<=0.1.7` exists on PyPI. This branch fixes that constraint in `pyproject.toml` to `global-hotkeys>=0.1.0` and adds `pyinstaller>=6.0` to `dev` optional-dependencies so that `uv sync --extra dev` installs the build toolchain natively without ad-hoc pip steps. Streamlined `.github/workflows/ci.yml` and `release.yml`. `uv sync --dry-run` now resolves all 219 packages in 849ms, and all 571 tests pass. `ruff check .` and `ruff format --check .` passed; diff reviewed.

## Next step
1. Push `fix/ci-dependency-resolution` and open a PR with gh.
2. Wait for user review and merge.

## Open questions
- None. `uv sync --dry-run` and local tests verify dependency resolution cleanly.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Correct `global-hotkeys` constraint to `>=0.1.0` in `pyproject.toml`.
  Reason: highest version available on PyPI is 0.1.7; `>=0.6.0` was unsatisfiable and broke CI `uv sync`.
- Add `pyinstaller>=6.0` to `[project.optional-dependencies.dev]`.
  Reason: allows single cached `uv sync --extra dev` command in workflows without separate pip install steps.
