# SESSION.md

## Current milestone
**Wispr Flow Experience: Live Partial Streaming Preview in Pill**

## Current branch
`feat/live-partial-preview`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented live partial speech transcription and UI preview:
- `kural/engine/streaming.py` (91 lines):
  - `StreamingTranscriber`: runs a lightweight daemon loop taking periodic non-destructive snapshots of the growing audio buffer (`get_audio_data()`).
  - Gated emission: only transcribes when buffer has grown by at least 0.3s of fresh audio, avoiding redundant passes on unchanged audio.
  - Emits live interim phrases to `on_partial(text)` callback.
- `kural/ui/overlay.py`:
  - Added `update_partial_text(text)`: displays live speech words directly inside the floating soundwave pill as the user is speaking.
- `kural/runtime.py`:
  - Starts `StreamingTranscriber` when recording begins; stops it upon recording completion.
  - Pipes interim words directly into `overlay.update_partial_text()`.
- 3 new unit tests in `tests/engine/test_streaming.py` (374 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/live-partial-preview` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test speaking live to see interim words stream inside the animated waveform pill!

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
- Live partials: preview words only update the floating pill display; final authoritative batch transcription, flow disfluency cleanup, and caret typing run on the full buffer upon stop.
  Reason: gives instant visual reassurance without risking premature or unstable typing into the document.
