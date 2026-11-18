# SESSION.md

## Current milestone
**Configurable Clipboard Retention for Windows Clipboard History (Win+V, inspired by anomalyco/hex)**

## Current branch
`feat/clipboard-retention`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented configurable clipboard retention inspired by `anomalyco/hex` (`labs.keep_on_clipboard`):
- `kural/control/windows.py`:
  - Extended `insert_text_at_caret(text, delivery_method, restore_clipboard)` to accept `restore_clipboard: bool = True`.
  - When `restore_clipboard=False` (keep on clipboard mode), skips snapshotting prior clipboard and leaves the formatted transcript on the system clipboard for Windows Clipboard History (`Win+V`).
- `kural/runtime.py`:
  - Reads `clipboard.restore_clipboard` from config and passes it to `insert_text_at_caret()`.
- `kural/ui/settings_window.py`:
  - Added `[ ] Keep Dictations in Windows Clipboard History (Win+V)` checkbox in the UI Settings tab.
  - Serializes `clipboard.restore_clipboard` into configuration.
- `README.md`:
  - Documented clipboard history retention in Smart Text Highlights and updated test badge to 500 passing.
- Unit tests:
  - Added unit test in `tests/control/test_windows.py` testing clipboard paste without restore.
  - Updated `tests/ui/test_settings.py` verifying `restore_clipboard` setting serialization.
  - 500 total passing tests, 0 requiring GPU or mic, ruff clean.

## Next step
1. Push `feat/clipboard-retention` and open PR into `main` with `gh pr create`.
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
- Clipboard history retention: inspired by `anomalyco/hex` (`labs.keep_on_clipboard`).
  Reason: allows users who rely on Windows Clipboard History (`Win+V`) to access, re-paste, and pin recent voice dictations across applications.
