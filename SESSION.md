# SESSION.md

## Current milestone
**Wispr Flow Experience: Push-to-Talk & Hands-Free Double-Tap Lock**

## Current branch
`feat/push-to-talk-and-gestures`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented Wispr Flow push-to-talk interactions and double-tap gestures:
- `kural/runtime.py`:
  - Push-to-Talk (PTT): listens for hotkey release event (`on_dictation_release()`) via `global_hotkeys` key-up hooks to stop recording the moment the user releases the keys.
  - Double-Tap Hands-Free Lock: detects rapid successive hotkey presses (<450ms) to lock dictation open for long-form speech, ignoring key release until explicitly tapped again.
- `kural/ui/settings_window.py`:
  - Added "Interaction Mode" dropdown on the Hotkeys tab (`toggle` vs `push_to_talk`).
  - Added `[x] Double-Tap to Lock Hands-Free` checkbox and wired it to `hotkey.double_tap_to_lock` config.
- 2 new unit tests in `tests/test_runtime.py` covering PTT key release and double-tap hands-free lock transitions (353 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/push-to-talk-and-gestures` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test holding down `Ctrl+Space` while talking (PTT) or double-tapping to lock hands-free!

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
- PTT key-up binding: dynamically attaches release callback only when `recording_mode == "push_to_talk"`.
  Reason: eliminates redundant release events in default toggle mode.
- Gesture timing threshold: 450ms window for double-tap detection.
  Reason: matches standard Windows and macOS double-click latency expectations.
