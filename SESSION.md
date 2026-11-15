# SESSION.md

## Current milestone
**Wispr Flow Experience: Smart Voice Rewrites & Text Transforms**

## Current branch
`feat/smart-voice-rewrites`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented Wispr Flow smart voice editing and inline text transforms:
- `kural/engine/transforms.py` (119 lines):
  - Fast deterministic transforms: bullet lists (`• Item`), numbered lists (`1. Item`), title casing, uppercase, lowercase.
  - Natural language AI rewrites via air-gapped `LocalLLMFallback` for instructions (*"translate to Tamil"*, *"summarize"*, *"make formal"*).
- `kural/control/windows.py`: Added `get_selected_text()` to safely capture highlighted text across Windows applications via simulated copy with clipboard restoration.
- `kural/control/parser.py`: Added voice transform triggers:
  - *"make that a bullet list"*, *"bullet that"*, *"வரிசைப்படுத்து"*.
  - *"title case that"*, *"தலைப்பாக்கு"*, *"uppercase that"*, *"பெரிய எழுத்தாக்கு"*.
  - *"make that [instruction]"*, *"rephrase that [instruction]"*.
- `kural/control/executor.py`: Wired `intent.kind == "transform"` to grab highlighted text (or fall back to the last dictation take in the ledger), execute the transform, and paste the rewritten text directly over the selection.
- 8 new unit tests in `tests/engine/test_transforms.py` (351 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/smart-voice-rewrites` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test highlighting text in any app and saying *"bullet that"* or *"make that title case"*!

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
- Smart Transforms: prioritizes instant deterministic transforms (bullets, casing) and falls back to local air-gapped LLM for complex instructions.
  Reason: zero-latency for standard edits; full power of LLMs for creative rewriting.
- Target fallback: if no text is actively highlighted on screen, transforms automatically operate on the user's last dictation take.
  Reason: eliminates the need to manually select text if you just finished speaking.
