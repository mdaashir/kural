# SESSION.md

## Current milestone
**Post-M5: Local OpenAI-Compatible Speech API Server**

## Current branch
`feat/openai-compatible-server`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented local OpenAI-compatible Whisper speech API server:
- `kural/engine/server.py` (284 lines):
  - Zero extra framework dependencies: built with stdlib `http.server.ThreadingHTTPServer`.
  - Implements the standard OpenAI audio API endpoints:
    - `POST /v1/audio/transcriptions`: multipart/form-data upload parsing audio (`file`), optional `language`, `prompt`, and `response_format` (`json` vs `text`).
    - `GET /v1/models`: OpenAI-compatible model listing (`whisper-1`).
    - `GET /health`: liveness probe returning engine and status.
  - Multi-format audio decoding: parses audio bytes via `soundfile` with stdlib `wave` fallback (resampling to 16 kHz float32).
  - Thread-safe serialized GPU model execution with `threading.Lock`.
  - Strict local privacy: bound to `127.0.0.1` loopback by default.
- `kural/__main__.py`: Added `--serve`, `--host` (default `127.0.0.1`), and `--port` (default `7777`) CLI commands.
- 6 new unit tests in `tests/engine/test_server.py` (325 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/openai-compatible-server` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test transcribing via local tools or curl: `curl -F file=@sample.wav http://127.0.0.1:7777/v1/audio/transcriptions`!

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
- Local API server: built with stdlib `http.server` instead of pulling heavy frameworks like FastAPI/Uvicorn.
  Reason: zero extra dependencies, instant startup, minimal footprint.
- Loopback binding: defaults strictly to `127.0.0.1`.
  Reason: prevents exposing the GPU speech model or local transcription capabilities to external networks.
