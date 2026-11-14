# SESSION.md

## Current milestone
**M4** — One installer, idle VRAM unload, elevated-window message

## Current branch
`feat/m4-installer-vram-elevation`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Delivered Milestone M4 requirements:
- `kural/engine/whisper_engine.py`: Configurable idle VRAM unload timer (`idle_unload_minutes`, default: 5 min) freeing GPU memory after inactivity and seamlessly waking up on the next dictation.
- `kural/config/config.defaults.yaml`: Added `idle_unload_minutes: 5`.
- `kural/control/windows.py`: Implemented `is_window_elevated(hwnd)` and `check_foreground_elevation()` to detect Administrator windows and issue clear actionable messages instead of silent UIPI input drops.
- `kural/doctor.py`: Added Idle VRAM unload status display.
- `packaging/kural.spec` & `packaging/build.bat`: PyInstaller standalone specification and build script producing `dist/kural/kural.exe`.
- 7 new unit tests in `tests/engine/test_vram_idle.py` and `tests/control/test_elevation.py` (211 total passing tests, 0 requiring GPU or mic, ruff clean).

## Next step
1. Push `feat/m4-installer-vram-elevation` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. After merge: Milestone M5 (optional) / final system evaluation.

## Open questions
- None blocking M4.

## Verify items (from AGENTS.md)
- [ ] **Hotkey-driven only?** AGENTS.md says "Neither appears to offer hands-free activation …
      Both are hotkey-driven (verify)." Confirm in both source repos before M5 planning.
- [x] **Feature overlap between base and donor** — Confirmed and resolved.
- [x] **Tamil voice commands supported** — Both formal Tamil and colloquial Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Package manager: `uv` + `pyproject.toml` (hatchling backend). Reason: matches system uv
  available on dev machine; avoids setup.py legacy.
- Linter: `ruff` only. Reason: handles pycodestyle + isort + pyupgrade in one tool.
- Sub-package layout: `engine/`, `control/`, `config/`, `ui/` as top-level siblings under `kural/`.
  Reason: clean separation of concerns; each milestone targets exactly one sub-package.
- Packaging chosen: PyInstaller one-folder standalone build (`packaging/kural.spec`).
  Reason: bundles Python 3.12, CTranslate2 DLLs, and YAML configs without requiring external installers.
- Elevated window handling: inspects `TokenElevation` via `OpenProcessToken` and warns user.
  Reason: Windows UIPI blocks synthetic input sent from medium to high-integrity windows.
