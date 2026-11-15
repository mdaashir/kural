# SESSION.md

## Current milestone
**Post-M5: Graphical History Window**

## Current branch
`feat/history-window-gui`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented searchable graphical history browser:
- `kural/ui/history_window.py` (282 lines):
  - Self-contained Tkinter dialog matching Kural's dark theme palette (`#0d1117`).
  - Search bar with live search-as-you-type querying `search_history()` (BM25 ranking).
  - Treeview displaying timestamps, task tag (`transcribe` vs `command`), foreground app, and transcribed text.
  - Double-click and "Copy Selected" button for one-click clipboard copying.
  - Singleton guard to ensure re-opening raises and focuses the existing window rather than stacking multiple instances.
- `kural/ui/tray.py`: Added `on_open_history` callback and `"History..."` tray menu item.
- `kural/runtime.py`: Connected tray `"History..."` to `open_history_window()`.
- `kural/__main__.py`: Added `--history-gui` CLI flag to launch the history window directly.
- 6 new unit tests in `tests/ui/test_history_window.py` + updated `tests/ui/test_tray.py` (307 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/history-window-gui` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test browsing past dictations graphically via `python -m kural --history-gui`!

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
- Graphical History Browser: pure Tkinter without heavy external GUI frameworks.
  Reason: native, instant startup, lightweight, and works seamlessly with dark Windows 11 desktop theme.
- Singleton window guard: only one instance of the History Window exists at a time; subsequent triggers lift and focus the window.
  Reason: prevents clutter and memory leaks from multiple open windows.
