# SESSION.md

## Current milestone
**Post-M5: Application Rules & Formatting Styles**

## Current branch
`feat/app-rules-and-styles`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Implemented per-application formatting styles and delivery rules:
- `kural/config/app_rules.defaults.yaml` (68 lines): Shipped default rules covering:
  - `password-managers`: (`1password`, `bitwarden`, `keepass`, `lastpass`) -> `suppress: true` to prevent dictation into password fields.
  - `terminals`: (`wt.exe`, `cmd.exe`, `powershell.exe`, `pwsh.exe`) -> `style: verbatim`.
  - `code-editors`: (`code.exe`, `cursor.exe`, `windsurf.exe`, `pycharm`) -> `style: verbatim`.
  - `chat-apps`: (`slack`, `discord`, `whatsapp`, `teams`) -> `style: casual`.
  - `email-and-docs`: (`outlook`, `thunderbird`, `winword.exe`, `gmail`) -> `style: formal`.
- `kural/control/app_rules.py` (150 lines): Evaluates foreground window `(exe, title)` against layered rules (`%APPDATA%\kural\app_rules.yaml` over shipped defaults), and provides `apply_formatting_style()` (`formal`, `casual`, `verbatim`).
- `kural/control/windows.py`: Added `get_foreground_window_info()` to capture active app metadata cleanly.
- `kural/runtime.py`: Integrated app rules into the dictation loop before text insertion:
  - Checks if delivery is suppressed (password managers).
  - Applies contextual formatting style (`verbatim` vs `formal` vs `casual`).
- 9 new unit tests in `tests/control/test_app_rules.py` (287 total passing, 0 requiring GPU, mic, or network, ruff clean).

## Next step
1. Push `feat/app-rules-and-styles` and open PR into `main` with `gh pr create`.
2. Wait for user to review and merge.
3. Test dictation in VS Code (verbatim) vs Outlook/Word (formal) live!

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
- Password managers: delivery is explicitly suppressed when a password manager is the foreground window.
  Reason: critical security protection preventing speech from leaking into credentials fields.
- Contextual formatting: terminals and code editors receive raw verbatim text; chat apps receive casual text; documents receive formal full sentences.
  Reason: eliminates manual punctuation cleanup across different types of applications.
