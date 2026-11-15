# SESSION.md

## Current milestone
**Post-M5: Hotkeys & Voice Commands Cheat Sheet**

## Current branch
`feat/hotkeys-cheat-sheet`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented dynamic hotkeys and voice commands quick-reference cheat sheet:
- `kural/ui/cheat_sheet.py` (245 lines):
  - Self-contained Tkinter dialog matching Kural's dark GitHub-palette (`#0d1117`).
  - Dynamically reads the user's active hotkeys from `ConfigManager` (`Ctrl+Space`, `Ctrl+Shift+Space`).
  - Displays structured sections for:
    1. **Global Hotkeys**: dictation and command trigger bindings with usage instructions.
    2. **Voice Control Triggers**: app open/switch, close, window ops, volume/media, and Tamil triggers (*open chrome*, *திற chrome*, *notepad மூடு*).
    3. **Inline Snippets**: `${date}`, `${time}`, `${clipboard}` speech expansions.
  - Singleton guard: re-invoking from CLI or tray raises and focuses the open instance.
- `kural/ui/tray.py`: Added `on_open_cheat_sheet` callback and `"Cheat Sheet..."` context menu item.
- `kural/runtime.py`: Connected tray `"Cheat Sheet..."` action to `open_cheat_sheet()`.
- `kural/__main__.py`: Added `--cheat-sheet` CLI command.
- 5 new unit tests in `tests/ui/test_cheat_sheet.py` + updated `tests/ui/test_tray.py` (330 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/hotkeys-cheat-sheet` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test launching the reference card via `python -m kural --cheat-sheet`!

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
- Cheat sheet design: pure Tkinter dialog displaying live hotkeys from `ConfigManager` instead of hardcoded defaults.
  Reason: guarantees the reference card always reflects the user's actual bindings.
