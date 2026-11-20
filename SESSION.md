# SESSION.md

## Current milestone
**Prevent Incognito transcripts from entering recovery ledger**

## Current branch
`fix/incognito-ledger-retention`

## PR
PR to be opened with gh after verification passes.

## Last completed step
PR #83 merged into main. Reproduced a privacy gap: `_process_audio()` wrote transcribed text to the in-memory `Ledger` even when incognito was active, on both successful insertion and failed-delivery fallback paths. `paste_last()` then remained able to retrieve that supposedly unsaved transcript. This branch gates both ledger writes on `not incognito`, clears preexisting ledger content when incognito is enabled, and disables Paste Last while incognito is active. A thread-safe `Ledger.clear()` clears text and metadata. Tests use a real Ledger and verify successful/failed dictation is not retained, history is not written, and paste_last does not insert text. `ruff check .`, `ruff format --check .`, and `pytest -q` passed (568 tests); diff reviewed.

## Next step
1. Push `fix/incognito-ledger-retention` and open a PR with gh.
2. Wait for user review and merge.

## Open questions
- The failed-delivery popup displays the current transcript for immediate recovery while Incognito is active; it is not retained in the ledger/history afterward.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Incognito mode clears the in-memory recovery ledger on entry, does not write new ledger text, and disables Paste Last until Incognito is off.
  Reason: align recoverability behavior with the privacy promise that incognito transcripts are not retained.
