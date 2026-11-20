# SESSION.md

## Current milestone
**Refresh API, privacy, and project handoff documentation**

## Current branch
`docs/refresh-api-and-privacy-docs`

## PR
PR to be opened with gh after verification passes.

## Last completed step
PR #86 merged into main. Audited all project-authored Markdown files. The README had stale Incognito wording, lacked local transcription API usage details, and its test badge was out of date. This branch documents Incognito’s history/learning/audio/ledger behavior and adds the verified loopback API routes, request fields, response formats, audio decode/resample behavior, 500 MiB limit, and curl example. `memory.md` had an old commit/test count; its historical M0–M5 summary is preserved while current state and next steps are refreshed. `AGENTS.md` and `THIRD_PARTY_NOTICES.md` are unchanged.

## Next step
1. Run required Ruff/pytest gates, review docs diff, then push `docs/refresh-api-and-privacy-docs` and open a PR with gh.
2. Wait for user review and merge.

## Open questions
- None for the documentation claims in this branch; the local API CLI flag and default port were checked against `kural/__main__.py` and the server constants.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Update README with API usage and privacy behavior; refresh memory.md current state without rewriting its historical roadmap; leave governing and license files unchanged.
  Reason: satisfy the requested full-doc iteration while preserving provenance and project instructions.
