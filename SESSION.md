# SESSION.md

## Current milestone
**M1** — GPU Turbo for EN + TA, benchmark harness

## Current branch
`test/benchmark-harness`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented ASR benchmark harness in `benchmarks/`:
- `metrics.py`: Levenshtein distance, WER, CER (supporting Tamil script and Tanglish), RTF.
- `datasets.py`: Benchmark dataset manager with automatic synthetic 16 kHz WAV generator.
- `run.py`: CLI benchmark tool with Markdown and JSON report generation.
- `tests/test_benchmark.py`: Pure unit tests for metrics and runner with mocked engine (133 tests passing, 0 requiring GPU).

## Next step
1. Push `test/benchmark-harness` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. After merge: run live benchmark on RTX 3050 (`large-v3-turbo` vs `distil-large-v3.5` vs `large-v3`) and record performance metrics.
4. Begin Milestone M2: port voice-control engine from donor into `kural/control/`.

## Open questions
- None blocking M1.

## Verify items (from AGENTS.md)
- [ ] **Hotkey-driven only?** AGENTS.md says "Neither appears to offer hands-free activation …
      Both are hotkey-driven (verify)." Confirm in both source repos before M5 planning.
- [ ] **Feature overlap between base and donor** — AGENTS.md says "some features may overlap …
      (verify before porting anything)." Check before port/control-engine starts.

## Decisions recorded (this session)
- Package manager: `uv` + `pyproject.toml` (hatchling backend). Reason: matches system uv
  available on dev machine; avoids setup.py legacy.
- Linter: `ruff` only. Reason: handles pycodestyle + isort + pyupgrade in one tool.
- Sub-package layout: `engine/`, `control/`, `config/`, `ui/` as top-level siblings under `kural/`.
  Reason: clean separation of concerns; each milestone targets exactly one sub-package.
- pytest markers defined: `gpu`, `mic`, `slow`. Reason: CI can deselect hardware-dependent
  tests with `-m 'not gpu and not mic'`.
- Benchmark metrics compute Character Error Rate (CER) alongside WER. Reason: essential for
  evaluating Tamil script and agglutinative suffixes.
- Reference audio files are generated on the fly via `create_synthetic_wav` if not already present,
  keeping git history binary-free as required by AGENTS.md.
