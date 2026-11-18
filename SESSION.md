# SESSION.md

## Current milestone
**Configurable Native vs. Roman Tamil Script Output**

## Current branch
`feat/indic-script-roman-option`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented configurable native vs. Roman-script Tamil output:
- `kural/engine/whisper_engine.py`:
  - Added `ROMAN_PRIMER_TAMIL` ("Aamaa, naalai meeting evvalavu manikku? Naan konjam late-aa varuven.") to steer Whisper toward Latin Tanglish chat output.
  - Added `indic_script` ("native" vs "roman") configuration parameter to `WhisperEngine`.
  - When `indic_script == "roman"` and `language == "ta"`, Whisper is steered with `ROMAN_PRIMER_TAMIL`; otherwise with `SCRIPT_PRIMER_TAMIL`.
- `kural/config/config.defaults.yaml`:
  - Added `whisper.indic_script: native` (options: `native`, `roman`).
- `kural/config/configcheck.py`:
  - Added `VALID_INDIC_SCRIPTS = {"native", "roman"}` with auto-fallback to `"native"`.
- `kural/runtime.py`:
  - Passed `indic_script` from config to `WhisperEngine`.
- `kural/ui/settings_window.py`:
  - Added Tamil Script Style dropdown (`native`, `roman`) in the Speech Engine tab.
  - Persisted `whisper.indic_script` in `collect_settings()`.
- Unit tests:
  - Added test in `tests/engine/test_whisper_engine.py` for Roman prompt injection.
  - Added test in `tests/config/test_configcheck.py` for schema validation.
  - Updated `tests/ui/test_settings.py` (424 total passing, 0 requiring GPU or mic, ruff clean).

## Next step
1. Push `feat/indic-script-roman-option` and open PR into `main` with `gh pr create`.
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
- Roman transliteration option: kept from donor repo per AGENTS.md Architecture Decisions ("Native Tamil script output; Roman option kept from donor").
  Reason: enables users who prefer Tanglish chat typing in Latin characters without forcing Tamil script.
