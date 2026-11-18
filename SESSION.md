# SESSION.md

## Current milestone
**Settings UI Controls for Mouse PTT and Delivery Method**

## Current branch
`feat/settings-ui-mouse-and-delivery`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Added graphical controls to `SettingsWindow`:
- `kural/ui/settings_window.py`:
  - Added Mouse Push-to-Talk Combobox (`""`, `"x1"`, `"x2"`, `"both"`, `"middle"`) to Hotkeys tab.
  - Added Text Delivery Method Combobox (`"paste"` via clipboard or `"type"` via direct `SendInput` keystrokes) to Overlay & Control tab.
  - Updated `collect_settings()` to persist `hotkey.mouse_button` and `clipboard.delivery_method`.
- Updated unit test in `tests/ui/test_settings.py` (416 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/settings-ui-mouse-and-delivery` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Open Settings window from system tray to easily configure mouse buttons and text delivery mode!

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
- Mouse button empty string: represents disabled mouse push-to-talk.
  Reason: clean fallback to keyboard-only hotkeys without error.
