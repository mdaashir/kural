# SESSION.md

## Current milestone
**Post-M5: Visual Overlay & System Tray** (desktop polish)

## Current branch
`feat/system-tray-and-overlay`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Added the desktop visual surface to Kural:
- `kural/ui/overlay.py` (239 lines): Floating, always-on-top, click-through Tkinter status pill showing live microphone level while recording, a processing indicator while transcribing, and green/red success/failure flashes. Runs on its own daemon thread with a thread-safe command queue.
- `kural/ui/tray.py` (111 lines): Optional Windows notification area icon via `pystray` with a context menu (Dictate, Voice Command, Exit). Gracefully degrades to a no-op when `pystray`/`Pillow` are absent.
- `kural/runtime.py`: Wires the overlay and tray into the state machine, so pressing `ctrl+space` or `ctrl+shift+space` immediately shows the pill.
- `kural/config/config.defaults.yaml`: Added `overlay` (enabled, position, click_through) and `system_tray` (enabled) configuration blocks.
- `pyproject.toml`: Split dependencies into `runtime`, `tray`, and `vad` optional extras so the core package stays installable on a bare Python.
- `kural/doctor.py`: Reports the new optional dependencies.
- 15 new unit tests in `tests/ui/test_overlay.py` and `tests/ui/test_tray.py` (248 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/system-tray-and-overlay` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. After merge: install the `runtime` extras on this machine and do the first real end-to-end dictation test in Notepad.

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
- Overlay uses only Python's built-in Tkinter (no new dependency) and is click-through on Windows
  via `WS_EX_TRANSPARENT | WS_EX_LAYERED`. Reason: zero-dependency visual feedback.
- Tray icon and audio runtime are optional extras, never hard dependencies.
  Reason: keeps `pip install kural` lightweight and lets the library run headless on CI.
