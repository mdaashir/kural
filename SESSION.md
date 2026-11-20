# SESSION.md

## Current milestone
**Preserve binary upload data containing multipart boundary-like bytes**

## Current branch
`fix/server-multipart-boundary-binary`

## PR
PR to be opened with gh after verification passes.

## Last completed step
PR #85 merged into main, adding incomplete-body checks. Reproduced a separate multipart bug: `_parse_multipart()` split raw bytes on the boundary token anywhere, truncating valid binary file payloads that contained the same byte sequence. This branch uses the standard-library email MIME parser to recognize delimiter lines and preserve payload bytes, while retaining the request size and Content-Length checks. Regression verifies repeated boundary-like bytes inside the file payload are returned intact. `ruff check .`, `ruff format --check .`, and `pytest -q` passed (570 tests); diff reviewed.

## Next step
1. Push `fix/server-multipart-boundary-binary` and open a PR with gh.
2. Wait for user review and merge.

## Open questions
- The parser still relies on the standard-library MIME parser’s handling of malformed multipart structures; this fix specifically covers boundary-like data inside binary payloads.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed and resolved in M5.
- [x] **Feature overlap between base and donor** — Confirmed and resolved across M0-M5.
- [x] **Tamil voice commands supported** — SVO, SOV, and Tanglish supported.
- [x] **Idle VRAM unload implemented** — Configurable timer unloads model from VRAM after inactivity.
- [x] **Elevated window message implemented** — UIPI token inspection warns user with actionable advice.

## Decisions recorded (this session)
- Parse multipart bodies with Python's standard-library MIME parser instead of splitting raw data on boundary bytes.
  Reason: boundary tokens may legally occur inside arbitrary binary file payloads and are only delimiters in valid MIME framing positions.
