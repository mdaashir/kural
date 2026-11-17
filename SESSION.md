# SESSION.md

## Current milestone
**Direct Unicode Keystroke Injection & Fallback**

## Current branch
`feat/unicode-keystroke-injection`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented SendInput Unicode keystroke injection and fallback:
- `kural/control/windows.py`:
  - `type_text_at_caret(text)`: direct character-by-character typing using Win32 `SendInput` with `KEYEVENTF_UNICODE` (0x0004), completely bypassing the Windows clipboard.
  - Correctly encodes multi-byte Unicode (including Tamil script glyphs and UTF-16 surrogate pairs) and translates `\n` to `VK_RETURN`.
  - Paced inter-character timing (15ms) ensures busy target apps keep up without dropping characters.
  - `insert_text_at_caret(text, delivery_method)`: supports `"paste"` (clipboard + Ctrl+V) and `"type"`, automatically falling back to `type_text_at_caret()` if clipboard access fails (e.g. locked by another app).
- `kural/config/config.defaults.yaml`: Added `clipboard.delivery_method: paste` (`paste` or `type`).
- `kural/runtime.py`: Passed `delivery_method` from config to `insert_text_at_caret()`.
- 2 new unit tests in `tests/control/test_windows.py` (398 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/unicode-keystroke-injection` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test dictating into paste-blocked applications or with `delivery_method: type`!

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
- Fallback delivery: if clipboard copy fails due to lock contention, automatically fallback to `type_text_at_caret()`.
  Reason: guarantees the user's speech is never lost even if the Windows clipboard API is blocked.
- Unicode keystrokes: uses `KEYEVENTF_UNICODE` with UTF-16 surrogate pairs.
  Reason: ensures native non-ASCII typing (Tamil glyphs, accents, emojis) works regardless of active Windows keyboard layout.
