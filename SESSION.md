# SESSION.md

## Current milestone
**M2** — Voice-control engine ported (Part 1: App Index, Guardrails, Media)

## Current branch
`port/app-index-and-guardrails`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Ported foundational control modules from `ROHITCRAFTSYT/WhispLocal` (commit `315af36`) into `kural/control/`:
- `guardrails.py`: File deletion / destructive action blocking, autonomous transaction blocking, cancellable shutdown timer.
- `app_index.py`: Windows Start Menu shortcut scanner, UWP Store apps, built-in aliases, web fallback, and multi-tier fuzzy matching.
- `media.py`: Windows Core Audio volume endpoint control (`IAudioEndpointVolume` via ctypes) and media key simulation.
- 24 new unit tests across `tests/control/` (157 total tests passing, 0 requiring GPU or mic, ruff clean).

## Next step
1. Push `port/app-index-and-guardrails` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. After merge: build M2 Part 2 (`port/voice-control-engine`) — window management, intent parser, and command executor.

## Open questions
- None blocking M2 Part 1.

## Verify items (from AGENTS.md)
- [ ] **Hotkey-driven only?** AGENTS.md says "Neither appears to offer hands-free activation …
      Both are hotkey-driven (verify)." Confirm in both source repos before M5 planning.
- [x] **Feature overlap between base and donor** — Confirmed: base has GPU engine + config + doctor; donor has rich control + app index + guardrails. Successfully merging donor control engine into `kural/control/`.

## Decisions recorded (this session)
- Package manager: `uv` + `pyproject.toml` (hatchling backend). Reason: matches system uv
  available on dev machine; avoids setup.py legacy.
- Linter: `ruff` only. Reason: handles pycodestyle + isort + pyupgrade in one tool.
- Sub-package layout: `engine/`, `control/`, `config/`, `ui/` as top-level siblings under `kural/`.
  Reason: clean separation of concerns; each milestone targets exactly one sub-package.
- Upstream donor `whisp/commands.py` (1,900 lines) is decomposed into small modules under ~300
  lines each (`guardrails.py`, `app_index.py`, `media.py`, `windows.py`, `parser.py`).
  Reason: AGENTS.md code standards require modular single-responsibility files.
- Shutdown/restart requires a 60-second cancel window via `shutdown /s /t 60` and `shutdown /a`.
  Reason: guardrails against accidental destructive voice commands.
