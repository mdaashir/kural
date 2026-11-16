# SESSION.md

## Current milestone
**Wispr Flow Experience: In-Place Voice Editing, Replacements & Code Casing**

## Current branch
`feat/wispr-flow-voice-editing`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented Wispr Flow voice editing, phrase replacement, code casing, and structural line edits:
- `kural/engine/transforms.py` (288 lines):
  - In-place word & phrase replacements: `"replace [old] with [new]"`, `"swap [old] for [new]"`, `"delete the word [word]"`.
  - Code casing conversions: `camelCase`, `snake_case`, `kebab-case`, `PascalCase`, `CONSTANT_CASE`.
  - Enclosures & Markdown wrappers: quotes (`"..."`), parentheses (`(...)`), backticks (`` `...` ``), code blocks (` ```...``` `).
  - Structural line edits: sorting lines alphabetically (`transform_sort_lines`), line joining into one paragraph, deleting the last sentence.
  - Retained deterministic list transforms (bullets, numbers) and local LLM fallback.
- `kural/control/parser.py`:
  - Added regex patterns to recognize `"replace ... with ..."`, `"swap ... for ..."`, wrappers (*"wrap in quotes"*, *"backtick that"*, *"code block that"*), code casing (*"camelcase that"*, *"snake case"*), and structural line commands (*"sort these lines"*, *"delete last sentence"*).
- 13 new unit tests in `tests/engine/test_transforms.py` (366 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/wispr-flow-voice-editing` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test highlighting text in VS Code or Notepad and saying *"replace Monday with Tuesday"* or *"camelcase that"*!

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
- Voice replacement matching: uses word-boundary regex (`\bword\b`) to prevent accidental partial-word replacements.
  Reason: ensures changing "cat" doesn't corrupt "catch" or "certificate".
- Developer code casings: split across spaces, dashes, underscores, and camelCase boundaries before re-casing.
  Reason: robustly converts any source string into the requested identifier convention.
