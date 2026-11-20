# SESSION.md

## Current milestone
**Continuous Integration (CI) and Automated Release Workflows**

## Current branch
`chore/ci-build-release-workflows`

## PR
PR to be opened with gh after verification passes.

## Last completed step
PR #90 merged into main. Added full GitHub Actions CI/CD workflows under `.github/workflows/`:
1. `.github/workflows/ci.yml`:
   - Triggers on push and pull request targeting `main`, plus manual `workflow_dispatch`.
   - Runs on `windows-latest` with `astral-sh/setup-uv@v5` and Python 3.12.
   - Runs `ruff format --check .`, `ruff check .`, and the full offline test suite (`pytest -m "not gpu and not mic"`).
   - Builds Python wheel and sdist distributions (`uv build`) and uploads as artifacts.
   - Builds the standalone Windows executable (`kural.exe`) with PyInstaller, runs smoke tests (`kural.exe --version` and `kural.exe --doctor`), and archives `kural-windows-x64.zip`.
2. `.github/workflows/release.yml`:
   - Triggers on version tag pushes (`v*.*.*`) or manual `workflow_dispatch`.
   - Runs validation tests, builds wheel/sdist packages, packages the standalone Windows application `kural-windows-x64.zip`, and creates an official GitHub Release with assets attached.
Updated `README.md`, `memory.md`, and `SESSION.md`.

## Next step
1. Run local verification gates (`ruff`, `pytest`).
2. Commit, push `chore/ci-build-release-workflows`, and open a PR with gh.
3. Wait for user review and merge.

## Open questions
- Workflows are configured for GitHub-hosted `windows-latest` runners; physical GPU inference benchmark workflows remain local per `AGENTS.md`.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Use `windows-latest` with `astral-sh/setup-uv@v5` and Python 3.12 for native PyInstaller building and Win32 testing.
  Reason: guarantees authentic Windows environment for packaging `kural.exe` and testing Win32 components without cross-compilation.
- Upload standalone `kural-windows-x64.zip` and python package distributions as CI artifacts on PRs and as release assets on tag pushes.
  Reason: provides immediate testing and distribution binaries for every commit and official release.
