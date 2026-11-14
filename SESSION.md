# SESSION.md

## Current milestone
**M2** — Voice-control engine ported (Part 2: Windows, Parser, Executor)

## Current branch
`port/voice-control-engine`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Completed Milestone M2 voice-control engine by porting and adapting remaining donor components into `kural/control/`:
- `windows.py`: Window enumeration, focus via `SwitchToThisWindow`, graceful close via `WM_CLOSE`, state management (minimize, maximize, snap left/right).
- `parser.py`: Pure intent parser with second-pass misheard verb recovery (e.g. *"oben chrome"* -> *"open chrome"*).
- `executor.py`: Implements the 4-tier resolution hierarchy: `commands.yaml` exact -> built-in commands -> fuzzy app match -> web fallback.
- 29 new unit tests in `tests/control/` (186 total tests passing, 0 requiring GPU or mic, ruff clean).

## Next step
1. Push `port/voice-control-engine` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. After merge: proceed to Milestone M3 — Tamil & Tanglish command aliases and accuracy evaluation (`feat/tamil-command-aliases`).

## Open questions
- None blocking M2.

## Verify items (from AGENTS.md)
- [ ] **Hotkey-driven only?** AGENTS.md says "Neither appears to offer hands-free activation …
      Both are hotkey-driven (verify)." Confirm in both source repos before M5 planning.
- [x] **Feature overlap between base and donor** — Confirmed: base has GPU engine + config + doctor; donor has rich control + app index + guardrails. Successfully merged donor control engine into `kural/control/`.

## Decisions recorded (this session)
- Package manager: `uv` + `pyproject.toml` (hatchling backend). Reason: matches system uv
  available on dev machine; avoids setup.py legacy.
- Linter: `ruff` only. Reason: handles pycodestyle + isort + pyupgrade in one tool.
- Sub-package layout: `engine/`, `control/`, `config/`, `ui/` as top-level siblings under `kural/`.
  Reason: clean separation of concerns; each milestone targets exactly one sub-package.
- Upstream donor `whisp/commands.py` (1,900 lines) decomposed into 5 small modular files under ~300
  lines each (`guardrails.py`, `app_index.py`, `media.py`, `windows.py`, `parser.py`, `executor.py`).
  Reason: AGENTS.md code standards require modular single-responsibility files.
- Command resolution hierarchy strictly follows AGENTS.md:
  `commands.yaml` exact -> built-in commands -> fuzzy app match -> web fallback / unrecognized.
