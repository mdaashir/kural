# SESSION.md

## Current milestone
**Require exact local API server endpoint routes**

## Current branch
`fix/server-exact-routes`

## PR
PR to be opened with gh after verification passes.

## Last completed step
PR #74 merged into main. Reproduced route prefix bug: `GET /healthz` and `GET /v1/models-extra` matched valid endpoints because the handler used `startswith()`. This branch compares parsed URL paths exactly for GET and POST endpoints while preserving query strings on valid paths. Tests verify unknown prefixed routes return 404 and `/health?check=1` remains valid. `ruff check .`, `ruff format --check .`, and `pytest -q` passed (556 tests); diff reviewed.

## Next step
1. Push `fix/server-exact-routes` and open a PR with gh.
2. Wait for user review and merge.

## Open questions
- Local API remains loopback-only; tests exercise routes through a local mock HTTP server.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Match parsed URL paths exactly for local API routes while allowing query strings on those paths.
  Reason: unknown prefixed paths such as `/healthz` should return 404, while valid routes may still include query parameters.
