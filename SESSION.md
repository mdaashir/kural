# SESSION.md

## Current milestone
**M0** — Import base, rename, upstream tests green

## Current branch
`port/doctor-and-config`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Ported `kural/config/` (ConfigManager, defaults_merge, YAML defaults),
`kural/engine/hardware_detection.py` (probes NVIDIA GPU and CUDA DLLs),
and `kural/doctor.py` (CLI diagnostic health check wired into `kural.__main__`).
All 114 tests pass, ruff is clean, and `kural --doctor` ran successfully on
Windows 11 with the RTX 3050 6GB Laptop GPU detected.

## Next step
1. Push `port/doctor-and-config` and open PR into `main` using `gh pr create`.
2. Wait for user to merge.
3. After merge: start Milestone M1 — GPU Turbo benchmark harness (`test/benchmark-harness`).

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
- Config management layers `config.defaults.yaml` under `%APPDATA%\kural\user_settings.yaml`.
  Reason: user settings remain minimal and clean, default updates arrive automatically.
- Hardware detection checks PE imports and standard Windows DLL search order for cuBLAS and
  cuDNN. Reason: prevents silent inference hangs on the RTX 3050.
