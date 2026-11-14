# SESSION.md

## Current milestone
**M0** — Import base, rename, upstream tests green

## Current branch
`chore/import-base-engine`

## PR
Not yet opened — branch pushed, PR to be raised with gh.

## Last completed step
Committed engine package port from drajb/whisper-local (fcd87875) into
`kural/engine/` with 11 ported source files and 5 test modules covering
dictation_languages, dictation_cleanup, streaming_delivery, model_registry,
and whisper_engine. 84 tests pass, ruff clean.

## Next step
1. Push `chore/import-base-engine` and open PR into `main` with gh.
2. Wait for user to merge.
3. After merge: start M1 — GPU Turbo benchmark harness (feat/benchmark-harness).

## Open questions
- None blocking M0.

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
- WhisperEngine defaults changed from upstream (tiny/cpu/int8) to large-v3-turbo/cuda/float16
  to target the RTX 3050. Reason: AGENTS.md architecture decision.
- Tests inject fake `faster_whisper` and `ctranslate2` into sys.modules via
  `tests/engine/conftest.py` so the engine can be imported without real GPU deps.
  Reason: AGENTS.md rule — tests must not need a GPU or model.
