# SESSION.md

## Current milestone
**README Refresh**

## Current branch
`docs/readme-refresh`

## PR
PR to be opened with gh after verification passes.

## Last completed step
Updated README.md to reflect all 39 merged PRs:
- Architecture tree: added all new modules (cues.py, chords.py, mouse.py, audio_gain.py, streaming.py, recovery.py, notes.py, server.py, flow_formatting.py, adaptive.py, history.py, snippets.py, cheat_sheet.py, history_window.py, settings_window.py, elevation.py, autostart.py, app_rules.py, planner.py, tamil_parser.py).
- Feature highlights: Wispr Flow-style pill, synthesized cues, Mouse Flow PTT, chord PTT, Incognito Mode, Paste Last / Retry Last recovery, text delivery method.
- Configuration table: documents all key hotkey, clipboard, overlay, and audio settings.
- Privacy & Safety table: formalizes guarantees.
- Test count: 248 → 419.

## Next step
1. Push `docs/readme-refresh` and open PR into `main` with `gh pr create`.
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
- README reflects all features as of PR #39 merged.
- Test count badge updated: 248 → 419.
- Architecture tree expanded with all current modules.
