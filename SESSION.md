# SESSION.md

## Current milestone
**Mouse Push-to-Talk Trigger (Mouse Flow)**

## Current branch
`feat/mouse-push-to-talk`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented Win32 low-level mouse button push-to-talk:
- `kural/control/mouse.py` (187 lines):
  - `MouseButtonTrigger`: runs a `WH_MOUSE_LL` hook on a dedicated Win32 message-loop thread.
  - Intercepts and swallows events (`return 1`) for configured buttons (`middle`, `x1`, `x2`, or `both`) so the button's native action (e.g. browser Back) does not interrupt dictation.
  - Sub-millisecond non-blocking dispatch to daemon threads prevents mouse cursor stutter.
  - Safe thread shutdown via `PostThreadMessageW(WM_QUIT)` and `UnhookWindowsHookEx`.
- `kural/runtime.py`:
  - Automatically initializes and starts `MouseButtonTrigger` when `hotkey.mouse_button` is configured.
  - Cleans up hook on runtime shutdown.
- 7 new unit tests in `tests/control/test_mouse.py` (416 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/mouse-push-to-talk` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test holding mouse thumb button (X1/X2) to dictate with hands on mouse!

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
- Event swallowing: returns 1 in `WH_MOUSE_LL` hook for active trigger button.
  Reason: prevents browser Back or auto-scroll from navigating away during speech.
- Dedicated hook thread: runs Win32 `GetMessage` loop on its own thread with sub-millisecond callback offloading.
  Reason: prevents any mouse cursor hitching or Windows auto-unhooking due to timeout.
