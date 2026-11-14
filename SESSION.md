# SESSION.md

## Current milestone
**M5 (Optional)** — Local-LLM intent fallback, wake word

## Current branch
`feat/m5-locallm-and-wakeword`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Delivered Milestone M5 optional capabilities (both off by default):
- `kural/control/llm_fallback.py`: Local-LLM intent fallback querying an optional local GGUF/ONNX model to map novel phrasing to canonical commands, with strict air-gap sanitization and deterministic parser re-validation.
- `kural/engine/wake_word.py`: Hands-free keyword activation detector and listener thread.
- `kural/control/executor.py`: Wired `llm_fallback` as Tier 5 in the resolution hierarchy.
- `kural/config/config.defaults.yaml`: Added `llm_fallback` and `wake_word` configuration blocks.
- 16 new unit tests across `tests/control/test_llm_fallback.py` and `tests/engine/test_wake_word.py` (227 total passing tests, 0 requiring GPU or mic, ruff clean).

## Next step
1. Push `feat/m5-locallm-and-wakeword` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Roadmap milestones M0 through M5 are complete! Final integration review.

## Open questions
- All roadmap milestones complete.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed: neither base (`whisper-local`) nor donor (`WhispLocal`) contained native wake-word engines. Designed and implemented opt-in offline wake-word detector in M5.
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
- LLM intent fallback is strictly air-gapped: cannot execute code directly, must map to a
  canonical command that parses through `parse_command()` and clears guardrails.
  Reason: eliminates autonomous execution risks and hallucinated shell commands.
- Wake-word detector is off by default and uses energy envelope gating.
  Reason: keeps background CPU and battery consumption minimal.
