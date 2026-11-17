# SESSION.md

## Current milestone
**Whisper Mode Adaptive Audio Gain**

## Current branch
`feat/audio-gain-whisper-mode`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented Whisper Mode adaptive audio gain boosting:
- `kural/engine/audio_gain.py` (40 lines):
  - `boost_quiet_audio(audio, max_gain=8.0)`: scales quiet or whispered speech up to `TARGET_PEAK = 0.6` without clipping, while leaving normal speech untouched.
  - 99.9th percentile peak estimation: rejects pops, clicks, or brief mic taps so they don't suppress the gain calculation for the rest of the sentence.
  - Noise floor protection: audio below `SILENCE_PEAK = 1e-3` is treated as pure silence or muted mic and never boosted, avoiding ambient hiss amplification and Whisper hallucinations.
  - Pure numpy, zero extra dependencies, instantaneous (<0.1ms).
- `kural/config/config.defaults.yaml`: Added `audio.whisper_mode: {enabled: true, max_gain: 8.0}`.
- `kural/ui/settings_window.py`: Added `[x] Whisper Mode (boost quiet / whispered speech)` checkbox to the settings window.
- 6 new unit tests in `tests/engine/test_audio_gain.py` (396 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/audio-gain-whisper-mode` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test whispering softly into the microphone to see accurate transcription without raised voices!

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
- 99.9th percentile peak estimation: prevents loud clicks or keyboard clatter from blinding the adaptive gain estimator.
  Reason: guarantees consistent volume scaling across variable audio dynamics.
- Silence threshold gating: ignores clips under 1e-3 amplitude.
  Reason: prevents boosting room background hiss into hallucinated speech text.
