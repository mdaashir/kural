# SESSION.md

## Current milestone
**Wispr Flow Experience: Caret-Aware Insertion & Continuation Planning**

## Current branch
`feat/caret-aware-insertion-planner`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented caret context-aware text layout planning:
- `kural/control/planner.py` (103 lines):
  - `plan_insertion(text, before, keep_caps)`: inspects characters left of the caret to determine formatting:
    - Continuation: lowercases the initial letter of common English words (`and`, `the`, `because`, `which`, etc.) while protecting proper nouns and custom dictionary hotwords.
    - New sentence: capitalizes initial letter after `.`, `?`, `!`, newline, or beginning of document.
    - Spacing: adds connecting space when continuing words; attaches punctuation without spaces; takes no space after opener quotes/brackets.
- `kural/control/windows.py`: Added `get_text_before_caret()` to inspect text left of the caret via Win32 `GetGUIThreadInfo` and `SendMessageTimeoutW` (`WM_GETTEXT`, `EM_GETSEL`), skipping password fields for privacy.
- `kural/runtime.py`: Integrated `plan_insertion()` into the dictation delivery pipeline, automatically supplying custom dictionary hotwords to prevent lowercasing proper nouns.
- 9 new unit tests in `tests/control/test_planner.py` (390 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/caret-aware-insertion-planner` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test dictating in the middle of a sentence: see it seamlessly continue in lowercase with leading space!

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
- Caret context inspection: uses fast Win32 `SendMessageTimeoutW` (100ms timeout) and skips password fields.
  Reason: non-blocking, zero external dependencies, guarantees credentials fields are never probed.
- Proper noun protection: `keep_caps` combines user dictionary hotwords (`whisper.hotwords`) and unrecognized capitalized words.
  Reason: ensures brand names and personal names are never inappropriately lowercased mid-sentence.
