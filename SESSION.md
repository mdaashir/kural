# SESSION.md

## Current milestone
**Wispr Flow Experience: Flow Formatting & Disfluency Engine**

## Current branch
`feat/wispr-flow-formatting`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented Wispr Flow natural text transformation pipeline:
- `kural/engine/flow_formatting.py` (118 lines):
  - `strip_fillers()`: word-boundary safe removal of verbal disfluencies and hesitation fillers (*um*, *uh*, *er*, *ah*, *you know*).
  - Collapses stuttered false-start duplicate words (*"I I think"* -> *"I think"*, *"we we"* -> *"we"*).
  - `replace_spoken_punctuation()`: translates spoken punctuation triggers (English and Tamil) to actual symbols (*comma*, *period*, *full stop*, *question mark*, *exclamation point*, *new line*, *new paragraph*, *கமா*, *புள்ளி*, *கேள்விக்குறி*).
  - `format_flow_typography()`: cleans spacing around punctuation, strips awkward whitespace, and applies proper sentence capitalization.
  - `apply_flow_formatting()`: main entry point, respecting `is_verbatim` to preserve raw code/terminal input intact.
- `kural/runtime.py`: Connected `apply_flow_formatting()` to the dictation processing loop right before caret insertion.
- 11 new unit tests in `tests/engine/test_flow_formatting.py` (343 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/wispr-flow-formatting` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test natural flow dictation live: say *"um send the report comma because uh we are ready period"* and see it type *"Send the report, because we are ready."*!

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
- Flow formatting pipeline: deterministic regex-based transformation rather than a local LLM call.
  Reason: instantaneous execution (<1 ms latency), 100% predictable, zero additional VRAM consumption.
- Verbatim bypass: code editors and terminals configured with `style: verbatim` skip filler removal and spoken punctuation substitution.
  Reason: ensures code syntax, shell commands, and regexes are never altered.
