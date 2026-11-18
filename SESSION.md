# SESSION.md

## Current milestone
**End-to-End Self-Test Diagnostic (`--selftest`)**

## Current branch
`feat/selftest-cli`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented automated end-to-end self-test diagnostic (`kural --selftest`):
- `kural/selftest.py` (196 lines):
  - `_test_audio_capture()`: tests default microphone query, records 0.5s at native sample rate, verifies RMS energy > 1e-6 (surfaces actionable Windows Privacy settings fix if mic is blocked).
  - `_test_model_loadable()`: verifies configured Whisper model resolves in registry and checks local cache status.
  - `_test_end_to_end()`: exercises CTranslate2 inference pipeline end-to-end with a 2-second audio slice and reports latency.
  - `_test_clipboard()`: verifies non-destructive clipboard copy and paste with original content restoration.
  - `run_selftest() -> int`: executes all 4 stages, returning 0 if all pass or 1 with actionable failure hints.
- `kural/__main__.py`:
  - Added `--selftest` CLI flag to `argparse` and wired into `run_selftest()`.
- `THIRD_PARTY_NOTICES.md`:
  - Recorded provenance for `selftest.py` (ported from `src/whisper_key/selftest.py`).
- Unit tests:
  - 11 new unit tests in `tests/test_selftest.py` covering all 4 stages (success, silence failure, missing device, registry error, CUDA failure, clipboard round-trip and mismatch, and suite aggregation).
  - 443 total passing tests, 0 requiring GPU or mic, ruff clean.

## Next step
1. Push `feat/selftest-cli` and open PR into `main` with `gh pr create`.
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
- Self-test diagnostic: dynamic 4-stage operational validation distinct from static environment `--doctor`.
  Reason: complies with AGENTS.md requirements ("Packaging dirs, tests, self-test, CI-style tooling").
- Actionable failure hints: every stage returns `(reason, fix_hint)` on failure.
  Reason: gives users explicit steps to fix permissions, audio device issues, or CUDA drivers.
