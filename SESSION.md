# SESSION.md

## Current milestone
**Copy Only Delivery Method (`delivery_method: copy`, inspired by anomalyco/hex)**

## Current branch
`feat/copy-only-delivery`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented Copy Only text delivery method inspired by `anomalyco/hex` (`copy_only`):
- `kural/control/windows.py`:
  - Extended `insert_text_at_caret(text, delivery_method)` to support `delivery_method == "copy"`.
  - Places transcribed text on the system clipboard via `pyperclip.copy()` without simulating `Ctrl+V` or injecting keystrokes into the active window.
- `kural/runtime.py`:
  - When `delivery_method == "copy"`, overlay flashes **"Copied"** (instead of "Typed").
- `kural/config/configcheck.py`:
  - Added `VALID_DELIVERY_METHODS = {"paste", "type", "copy"}` and validation rule falling back to `"paste"` if unrecognized.
- `kural/ui/settings_window.py`:
  - Added `"copy"` to `DELIVERY_METHODS` list with updated descriptive helper text.
- `README.md`:
  - Documented `"copy"` delivery method in key highlights and updated test badge to 489 passing.
- Unit tests:
  - Added unit test in `tests/control/test_windows.py` testing copy only delivery without keystroke injection.
  - Added unit test in `tests/test_runtime.py` testing overlay "Copied" feedback.
  - Added unit test in `tests/config/test_configcheck.py` testing delivery method validation.
  - 489 total passing tests, 0 requiring GPU or mic, ruff clean.

## Next step
1. Push `feat/copy-only-delivery` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.

## Open questions
- None.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Copy Only delivery: inspired by `anomalyco/hex` (`labs.copy_only`).
  Reason: allows users to dictate notes or speech directly to their clipboard without overwriting selections or typing into focused windows.
