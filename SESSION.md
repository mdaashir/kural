# SESSION.md

## Current milestone
**Post-M5: Live Dictation & Voice Control Runtime**

## Current branch
`feat/live-dictation-runtime`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Built and integrated the end-to-end background daemon:
- `kural/runtime.py`: Coordinates the runtime state machine (`IDLE` <-> `RECORDING_DICTATION` / `RECORDING_COMMAND` <-> `PROCESSING`), global hotkey bindings (`ctrl+space` for dictation, `ctrl+shift+space` for commands), audio capture, GPU Whisper inference, caret insertion, and voice-control execution.
- `kural/control/windows.py`: Implemented `insert_text_at_caret(text)` with clipboard state preservation, Windows `Ctrl+V` key simulation, and foreground window elevation checking.
- `kural/__main__.py`: Connected to launch `KuralRuntime.run()` on `python -m kural`.
- 6 new unit tests in `tests/test_runtime.py` covering state transitions, dictation text typing, command routing, and empty audio resets (233 total tests passing, 0 requiring GPU or mic, ruff clean).

## Next step
1. Push `feat/live-dictation-runtime` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Live test dictation and voice commands directly in Windows apps!

## Open questions
- None. Full pipeline connected end-to-end.

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
- Clipboard preservation: `insert_text_at_caret` copies previous clipboard contents and restores
  them asynchronously after paste, preventing destruction of user's copied text.
- UIPI protection: foreground elevation is verified before pasting or macro execution to notify
  the user when Windows security blocks synthetic keystrokes.
