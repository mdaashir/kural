# SESSION.md

## Current milestone
**Post-M5: History Search & Productivity Stats**

## Current branch
`feat/history-and-stats`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented dictation history logging, BM25 full-text search, and productivity stats:
- `kural/engine/history.py` (188 lines):
  - Local JSONL logging to `%APPDATA%\kural\history.jsonl` recording text, task (`transcribe`/`command`), duration, app, and timestamp.
  - Dependency-free BM25 full-text ranking over historical dictations with prefix scoring.
  - `compute_stats()`: calculates total words dictated, speaking speed in WPM, time saved vs manual typing, active daily streak, and top apps.
- `kural/__main__.py`: Added CLI commands:
  - `python -m kural --history [query]`: searches past dictations using BM25 ranking.
  - `python -m kural --stats`: displays productivity statistics and streak.
- `kural/runtime.py`: Automatically appends completed dictations and commands to `history.jsonl`.
- 5 new unit tests in `tests/engine/test_history.py` (301 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/history-and-stats` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Review your personal dictation history and metrics live via `python -m kural --stats`!

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
- History storage: local `%APPDATA%\kural\history.jsonl`, strictly private with zero cloud telemetry.
  Reason: complies with core principles in AGENTS.md.
- Search algorithm: pure BM25 full-text ranking without third-party search dependencies.
  Reason: lightweight, lightning-fast ranking over thousands of speech records.
