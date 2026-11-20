# SESSION.md

## Current milestone
**Keep all project Markdown current with merged code and workflow state**

## Current branch
`docs/update-all-markdown-after-pr-87`

## PR
Documentation refresh PR to be opened with gh after verification passes.

## Last completed step
PR #87 merged into main; local `main` was synced before this documentation iteration. A follow-up audit found README's Privacy & Safety table omitted the in-memory Ledger/Paste Last behavior added in PR #84, while the README feature list already described it. This branch makes those sections consistent and updates the session/memory handoff to reflect PR #87's merge and the current verified project state. `AGENTS.md` and `THIRD_PARTY_NOTICES.md` are intentionally unchanged. Full tests currently report 570 passed; Ruff lint and format checks pass.

## Next step
1. Finish Markdown audit, run required checks, review diff, then push `docs/update-all-markdown-after-pr-87` and open a PR with gh.
2. Wait for user review and merge.

## Open questions
- None for the documentation changes; CLI and API claims were checked against implementation.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Keep `AGENTS.md` as governing workflow and preserve `THIRD_PARTY_NOTICES.md` unless a concrete attribution error is found.
  Reason: update all project-facing handoffs without weakening instructions or perturbing verified license text.
- Keep `memory.md` roadmap history, but refresh its current state and next steps instead of rewriting the historical record.
  Reason: preserve durable milestone context while removing stale operating status.
