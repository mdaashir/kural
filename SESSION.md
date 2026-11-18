# SESSION.md

## Current milestone
**Automatic Output Audio Ducking (inspired by anomalyco/hex)**

## Current branch
`feat/audio-output-ducking`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented output audio ducking inspired by `anomalyco/hex`:
- `kural/engine/audio_ducking.py` (111 lines):
  - `AudioDucker`: automatically and smoothly lowers system playback volume (music, videos, podcasts) when recording starts, preventing speaker audio from bleeding into the microphone.
  - Smooth 4-step ramp down (~100ms) on start, and smooth 5-step ramp up (~200ms) on restore to prevent audible clicks or pops.
  - User volume protection: if user manually adjusts system volume during dictation, restore is safely skipped to respect manual override.
- `kural/config/config.defaults.yaml`:
  - Added `audio.ducking: {enabled: false, factor: 0.25}`.
- `kural/config/configcheck.py`:
  - Added schema validation ensuring `0.0 <= factor <= 1.0` with automatic clamping.
- `kural/runtime.py`:
  - Initialized `AudioDucker` and wired `start()` into dictation/command start and `restore()` into recording finish/cancellation.
- `kural/ui/settings_window.py`:
  - Added `[ ] Audio Ducking (lower music/video volume while dictating)` checkbox to Settings.
- `README.md`:
  - Documented Audio Ducking in architecture tree and smart text features; updated test badge to 484 passing.
- Unit tests:
  - 5 new unit tests in `tests/engine/test_audio_ducking.py` covering factor clamping, ramp down and restoration, ducked state prevention, and restore no-ops.
  - Updated tests in `tests/config/test_configcheck.py` and `tests/ui/test_settings.py`.
  - 484 total passing tests, 0 requiring GPU or mic, ruff clean.

## Next step
1. Push `feat/audio-output-ducking` and open PR into `main` with `gh pr create`.
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
- Output audio ducking: inspired by `anomalyco/hex` (`src/audio/output_ducking.rs`).
  Reason: prevents background music/video playback from being picked up by the microphone and hallucinated by Whisper.
- Asynchronous ramp: volume ramp runs on daemon threads with 4/5 micro-steps.
  Reason: completely eliminates audio pops or harsh sudden volume jumps without blocking the recording thread.
