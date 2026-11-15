# SESSION.md

## Current milestone
**Post-M5: Adaptive Vocabulary & Custom Dictionary**

## Current branch
`feat/adaptive-vocabulary-and-dictionary`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented adaptive vocabulary learning and dictionary hotwords management:
- `kural/engine/dictionary.py` (104 lines):
  - Direct management of biased vocabulary (`whisper.hotwords`) in `%APPDATA%\kural\user_settings.yaml`.
  - Functions: `list_hotwords()`, `add_hotword(word)`, `remove_hotword(word)`.
- `kural/engine/adaptive.py` (146 lines):
  - Local on-disk personalization stored in `%APPDATA%\kural\adaptive.json`.
  - Tracks vocabulary frequencies from accepted dictations (safe for English and Tamil Unicode words).
  - Automatically identifies top domain terms and feeds them to Whisper as hotwords.
  - Learns and applies user-taught word corrections (e.g. replacing recurrent mishearings).
- `kural/__main__.py`: Added CLI commands:
  - `python -m kural --dict-list`
  - `python -m kural --dict-add <word>`
  - `python -m kural --dict-remove <word>`
- `kural/runtime.py`: Integrated `AdaptiveLearner` into the dictation loop to apply corrections and learn words on completed takes.
- 9 new unit tests in `tests/engine/test_dictionary.py` and `tests/engine/test_adaptive.py` (296 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/adaptive-vocabulary-and-dictionary` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test adding technical terms or Tamil proper nouns via `python -m kural --dict-add "..."` live!

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
- Adaptive vocabulary: runs 100% locally on disk (`adaptive.json`), zero network calls.
  Reason: strictly adheres to Kural's privacy guarantees.
- Stopwords filtering: filters high-frequency English functional words so hotwords slots are
  dedicated exclusively to domain terminology, names, and specialized jargon.
