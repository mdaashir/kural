# SESSION.md

## Current milestone
**Document current delivery, Incognito, and local API behavior**

## Current branch
`docs/current-delivery-incognito-api-behavior`

## PR
PR to be opened with gh after verification passes.

## Last completed step
PR #89 merged into main. This docs iteration follows up on three audit findings in README/config comments: the usage table omitted the Escape cancel action and Ctrl+Alt+V Paste Last binding, and the delivery-method docs omitted Copy Only. The API documentation is also being expanded to include structured inference failure responses and multipart error handling. `memory.md` is refreshed to the current branch/test status; `AGENTS.md` and `THIRD_PARTY_NOTICES.md` remain unchanged.

## Next step
1. Finish documentation review, run required checks, then push `docs/current-delivery-incognito-api-behavior` and open a PR with gh.
2. Wait for user review and merge.

## Open questions
- None for the documented behaviors; confirm claims against current runtime/config/server implementation before merge.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Document the actual supported delivery modes, Incognito recovery guarantees, and API request/error behavior without implying unimplemented response formats.
  Reason: keep user-facing docs aligned with current code and verified tests.
