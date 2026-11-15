# SESSION.md

## Current milestone
**Post-M5: Snippets & Never-Lose-a-Dictation Recovery**

## Current branch
`feat/snippets-and-recovery`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Built text snippets and never-lose-a-dictation recovery subsystems:
- `kural/engine/recovery.py` (174 lines):
  - `LastTake`: Encrypts raw 16 kHz audio on disk using Windows Data Protection API (DPAPI `CryptProtectData`). Only the current Windows user account can decrypt it. Automatically expires after 24 hours. Enables retrying a failed or interrupted dictation without speaking again.
  - `Ledger`: Ephemeral in-memory store of the last successfully inserted text.
- `kural/engine/snippets.py` (94 lines):
  - Spoken shortcuts expanding inline during dictation (e.g. *"today's date"* -> `2026-11-15`).
  - Supports dynamic variable interpolation (`${date}`, `${time}`, `${clipboard}`). Matches longest triggers first.
- `kural/control/parser.py`: Added voice commands for recovery:
  - *"paste last dictation"*, *"paste that again"*, *"கடைசி உரையை தட்டச்சு செய்"* -> calls `ledger.last()` and pastes at caret.
  - *"retry last take"*, *"retry last dictation"*, *"கடைசி பதிவை மீண்டும் செய்"* -> re-transcribes the cached take.
- `kural/runtime.py`: Integrates `LastTake`, `Ledger`, and `apply_snippets` into the dictation pipeline.
- 13 new unit tests in `tests/engine/test_recovery.py` and `tests/engine/test_snippets.py` (278 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/snippets-and-recovery` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test inline snippets (*"today's date"*) and *"paste last dictation"* live!

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
- Retained audio security: single-take raw audio is encrypted via Windows DPAPI `CryptProtectData`.
  Reason: strictly conforms to AGENTS.md privacy requirement ("Retained audio only DPAPI-encrypted, one take, short expiry").
- Text snippets: applied inline before caret insertion without requiring a separate hotkey.
  Reason: natural dictation shortcuts for dates, signatures, and clipboard text.
