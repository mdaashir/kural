# SESSION.md

## Current milestone
**Post-M5: Settings UI Window** (desktop configuration)

## Current branch
`feat/settings-ui`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Built the desktop Settings UI window:
- `kural/ui/settings_window.py` (268 lines): Tkinter notebook dialog with 3 tabs:
  - **Speech Engine**: Whisper model (`large-v3-turbo`, `distil-large-v3.5`, `large-v3`, etc.), device, compute precision, default language (`en`, `ta`, `auto`), and idle VRAM unload timeout (minutes).
  - **Hotkeys**: Dictation hotkey and Voice Command hotkey configuration.
  - **Overlay & Control**: Toggle status pill, overlay position dropdown, click-through toggle, and fuzzy command matching.
  - **Action bar**: Save (writes overrides to `%APPDATA%\kural\user_settings.yaml`), Cancel, and "Open Config Folder".
- `kural/__main__.py`: Added `--settings` CLI flag to launch the Settings window.
- `kural/ui/tray.py`: Added "Settings..." item to the notification area context menu.
- `kural/ui/__init__.py`: Exported `SettingsWindow` and `open_settings_window`.
- `kural/runtime.py`: Wired `open_settings()` callback to tray icon.
- 6 new unit tests in `tests/ui/test_settings.py` (254 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/settings-ui` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. After merge: run `python -m kural --settings` on the real machine to visually inspect the window.

## Open questions
- None.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed: neither base (`whisper-local`) nor donor (`WhispLocal`) contained native wake-word engines. Designed and implemented opt-in offline wake-word detector in M5.
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
- Settings window is built with standard Tkinter (zero external dependencies) and only writes
  user-modified overrides to `%APPDATA%\kural\user_settings.yaml` via `ConfigManager`.
- Testability: Settings extraction and saving logic is separated from Tk widget calls so unit tests
  run cleanly on headless environments without a display server.
