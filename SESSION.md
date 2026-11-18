# SESSION.md

## Current milestone
**Incognito Mode (Zero Retention & Privacy Mode)**

## Current branch
`feat/incognito-mode`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented Incognito Mode across the runtime and system tray:
- `kural/runtime.py`:
  - `self.incognito`: session privacy state toggle.
  - `toggle_incognito()`: toggles incognito, immediately clears `self.last_take` when activated, flashes `"Incognito On"` / `"Incognito Off"` on the overlay, and refreshes the tray menu.
  - Gated data persistence: in Incognito mode, `append_history(...)`, `self.adaptive.learn_text(...)`, and `self.last_take.save(...)` are completely bypassed so zero persistent speech text, vocabulary adjustments, or audio takes are retained on disk.
- `kural/ui/tray.py`:
  - Added checkable `Incognito (save nothing)` menu item with dynamic checkmark linked to `is_incognito()`.
  - Added `update_menu()` to reflect state changes immediately.
- 2 updated/new unit tests in `tests/test_runtime.py` and `tests/ui/test_tray.py` (417 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/incognito-mode` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test toggling Incognito from the tray icon to verify private dictation without disk logging!

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
- Incognito privacy guarantee: when active, neither history.jsonl, adaptive vocabulary, nor DPAPI-retained audio are saved to disk.
  Reason: fulfills AGENTS.md architecture decision ("Retained audio only DPAPI-encrypted, one take, short expiry, off in Incognito").
