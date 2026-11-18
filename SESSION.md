# SESSION.md

## Current milestone
**Rotating File Logging & Diagnostics**

## Current branch
`feat/rotating-log`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented rotating file logging and doctor integration:
- `kural/engine/log_setup.py`:
  - `setup_logging(config)`: configures root logger with console StreamHandler + `RotatingFileHandler` writing to `%APPDATA%\kural\kural.log` (1 MB max, 3 backups kept).
  - Respects `logging.level` (default `INFO`) and `logging.file.enabled`.
  - Transcripts are never logged at INFO (air-gapped text pipeline).
- `kural/__main__.py`:
  - Calls `setup_logging(cfg.config)` early in `main()` before runtime starts.
- `kural/doctor.py`:
  - Added `_section_logging()` diagnostic check: displays log level, log file path, rotation policy (1 MB, 3 backups), and transcript privacy guarantee.
- `tests/engine/test_log_setup.py`:
  - 3 unit tests verifying handler installation, rotation file writing, and disabled state (422 total tests passing, 0 requiring GPU or mic, ruff clean).

## Next step
1. Push `feat/rotating-log` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.

## Open questions
- None.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Logging setup: `RotatingFileHandler` at `%APPDATA%\kural\kural.log`, 1 MB x 3 backups, UTF-8.
  Reason: complies with Code standards in AGENTS.md ("Errors reach the user as a plain sentence in the UI and a full traceback in kural.log (rotating, 1 MB x 3)").
- Privacy gate: transcript text is never written to `kural.log` at INFO level.
  Reason: guarantees air-gapped dictation privacy.
