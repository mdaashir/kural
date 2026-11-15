# SESSION.md

## Current milestone
**Post-M5: Windows Startup (Autostart) Registration**

## Current branch
`feat/windows-autostart`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented Windows autostart registration and management:
- `kural/control/autostart.py` (112 lines):
  - Windows registry integration via stdlib `winreg` under `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` with value name `"Kural"`.
  - Windowless background execution: automatically resolves and runs via `pythonw.exe -m kural` so there is no console flash at Windows boot.
  - Safe opt-in functions: `is_autostart_enabled()`, `enable_autostart()`, `disable_autostart()`, and `get_stored_autostart_command()`.
- `kural/ui/settings_window.py`: Added `[x] Launch Kural at Windows Startup` checkbox to the "Overlay & Control" tab and synced it on save.
- `kural/doctor.py`: Added autostart status reporting in the runtime section of the doctor diagnostics report.
- `kural/__main__.py`: Added `--autostart-status`, `--enable-autostart`, and `--disable-autostart` CLI commands.
- 12 new unit tests in `tests/control/test_autostart.py` + updated `tests/ui/test_settings.py` (319 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/windows-autostart` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Verify status live with `python -m kural --autostart-status` or in the Settings UI!

## Open questions
- None.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Package manager: `uv` + `pyproject.toml` (hatchling backend). Reason: matches system uv
  available on dev machine; avoids setup.py legacy.
- Linter: `ruff` only. Reason: handles pycodestyle + isort + pyupgrade in one tool.
- Sub-package layout: `engine/`, `control/`, `config/`, `ui/` as top-level siblings under `kural/`.
  Reason: clean separation of concerns; each milestone targets exactly one sub-package.
- Windowless autostart: uses `pythonw.exe` for startup registration.
  Reason: prevents a black console terminal window from flashing when the user logs into Windows.
- Opt-in policy: startup registry entries are never written automatically without explicit user action in Settings or CLI.
  Reason: respects user choice and system hygiene.
