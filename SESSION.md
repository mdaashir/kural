# SESSION.md

## Current milestone
**Single-Instance Process Mutex & Graceful Takeover**

## Current branch
`feat/single-instance-lock`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented single-instance mutex and graceful takeover:
- `kural/engine/instance_manager.py`:
  - `acquire_single_instance_lock(app_name, timeout=5.0, allow_takeover=True)`: creates named Win32 mutex (`Local\Kural_SingleInstance`).
  - Graceful takeover: if another instance is already running, reads `%APPDATA%\kural\kural.pid`, signals old instance with `SIGTERM`, and polls for lock release up to 5s.
  - `write_pid_file(app_name)` / `cleanup_pid_file(app_name)`: tracks active process ID in `kural.pid`.
  - `release_single_instance_lock(handle, app_name)`: closes Win32 mutex handle and removes PID file.
- `kural/__main__.py`:
  - Acquires single-instance lock before starting background runtime; releases lock on shutdown.
- `THIRD_PARTY_NOTICES.md`:
  - Recorded provenance for `instance_manager.py` (ported from `src/whisper_key/instance_manager.py` + `src/whisper_key/platform/windows/instance_lock.py`).
- Unit tests:
  - 8 new unit tests in `tests/engine/test_instance_manager.py` covering PID file lifecycle, process termination, fresh lock acquisition, blocked without takeover, graceful takeover, and cleanup.
  - 432 total passing tests, 0 requiring GPU or mic, ruff clean.

## Next step
1. Push `feat/single-instance-lock` and open PR into `main` with `gh pr create`.
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
- Graceful takeover: launching Kural when already running replaces the previous background instance.
  Reason: complies with desktop user expectations when double-clicking desktop shortcut or restarting app.
- Mutex via ctypes: native Windows `CreateMutexW` without external heavy pywin32 dependency.
  Reason: lightweight and works out-of-the-box in standalone PyInstaller bundles.
