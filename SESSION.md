# SESSION.md

## Current milestone
**Voice Stop Phrase for Hands-Free Dictation (inspired by anomalyco/hex)**

## Current branch
`feat/voice-stop-phrase`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented voice stop phrase detection and transcript stripping inspired by `anomalyco/hex` (`labs.stop_phrase`):
- `kural/engine/stop_phrase.py` (74 lines):
  - `StopPhraseMatcher`: detects spoken finish phrases at the end of streaming interim speech.
  - Supports English (`"stop dictation"`, `"stop recording"`) and Tamil/Tanglish aliases (`"முடி"`, `"நிறுத்து"`, `"stop பண்ணு"`).
  - `strip_stop_phrase(text)`: cleanly removes trailing stop phrases and associated punctuation from finalized transcripts.
- `kural/runtime.py`:
  - Initialized `StopPhraseMatcher` and fed incoming partial text from `_on_live_partial()`.
  - When matched during hands-free dictation (`toggle` or double-tap locked mode), immediately auto-finalizes recording on a background thread and cleanly strips the stop phrase before typing.
- `kural/config/config.defaults.yaml`:
  - Added `hotkey.stop_phrase: {enabled: false, phrases: [...]}`.
- `kural/config/configcheck.py`:
  - Added validation for `hotkey.stop_phrase.phrases`.
- `kural/ui/settings_window.py`:
  - Added `[ ] Voice Stop Phrase (say 'stop dictation' to finish hands-free)` checkbox in Hotkeys tab.
- `README.md`:
  - Added `stop_phrase.py` to architecture tree, documented feature in highlights, and updated test badge to 499 passing.
- Unit tests:
  - 9 new unit tests in `tests/engine/test_stop_phrase.py` covering matching, case-insensitivity, Tamil phrases, mid-sentence protection, and clean stripping.
  - Unit test in `tests/test_runtime.py` verifying auto-stopping and phrase stripping.
  - Updated `tests/ui/test_settings.py` for `stop_phrase` serialization.
  - 499 total passing tests, 0 requiring GPU or mic, ruff clean.

## Next step
1. Push `feat/voice-stop-phrase` and open PR into `main` with `gh pr create`.
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
- Voice stop phrase: inspired by `anomalyco/hex` (`labs.stop_phrase`).
  Reason: allows hands-free dictation from a distance or with hands occupied, cleanly dropping the trigger phrase from typed text.
- Punctuation & prefix tolerance: stripped without slicing off prior sentence-ending periods.
  Reason: preserves grammatically complete sentences before the stop phrase.
