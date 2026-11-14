# SESSION.md

## Current milestone
**M3** — Tamil + Tanglish command aliases and test set

## Current branch
`feat/tamil-command-aliases`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented bilingual (Tamil and Tanglish) voice-control support across Kural:
- `kural/control/parser.py`: Extended with SOV (*"chrome திற"*, *"calculator open பண்ணு"*) and SVO (*"திற chrome"*, *"close notepad"*) patterns, Tamil media/volume controls, and Tamil YouTube/web search.
- `kural/control/app_index.py`: Added Tamil application and site aliases (*"குரோம்"*, *"நோட்பேடு"*, *"கால்குலேட்டர்"*, *"யூடியூப்"*).
- `kural/config/commands.defaults.yaml`: Added pre-configured Tamil & Tanglish voice commands.
- `kural/engine/whisper_engine.py`: Injected native Tamil script primer (`SCRIPT_PRIMER_TAMIL`) when `language == "ta"` to steer Whisper toward Tamil Unicode.
- `benchmarks/datasets.py`: Added Tamil command test clips to the benchmark test manifest.
- 18 new unit tests in `tests/control/test_tamil_parser.py` and `tests/engine/test_whisper_engine.py` (204 total passing tests, 0 requiring GPU or mic, ruff clean).

## Next step
1. Push `feat/tamil-command-aliases` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. After merge: proceed to Milestone M4 — Installer, idle VRAM unload, elevated-window message (`feat/idle-vram-unload`).

## Open questions
- None blocking M3.

## Verify items (from AGENTS.md)
- [ ] **Hotkey-driven only?** AGENTS.md says "Neither appears to offer hands-free activation …
      Both are hotkey-driven (verify)." Confirm in both source repos before M5 planning.
- [x] **Feature overlap between base and donor** — Confirmed: base has GPU engine + config + doctor; donor has rich control + app index + guardrails. Successfully merged donor control engine into `kural/control/`.
- [x] **Tamil voice commands supported** — Both formal Tamil and colloquial Tanglish (with auxiliary *பண்ணு*) fully supported in parser, aliases, and YAML defaults.

## Decisions recorded (this session)
- Package manager: `uv` + `pyproject.toml` (hatchling backend). Reason: matches system uv
  available on dev machine; avoids setup.py legacy.
- Linter: `ruff` only. Reason: handles pycodestyle + isort + pyupgrade in one tool.
- Sub-package layout: `engine/`, `control/`, `config/`, `ui/` as top-level siblings under `kural/`.
  Reason: clean separation of concerns; each milestone targets exactly one sub-package.
- Tamil syntax supports both SVO (*"திற chrome"*) and SOV (*"chrome திற"*, *"chrome open பண்ணு"*).
  Reason: reflects natural speech patterns of bilingual Tamil Windows users.
- Injected `SCRIPT_PRIMER_TAMIL` in `WhisperEngine` when `language == "ta"`.
  Reason: prevents Whisper from falling back to Romanized phonetic script.
