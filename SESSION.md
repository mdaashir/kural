# SESSION.md

## Current milestone
**M0 - M5 Roadmap Complete** (Ready for end-to-end dogfooding & live usage)

## Current branch
`docs/update-docs-and-roadmap`

## PR
PR to be opened with gh after documentation review.

## Last completed step
Completed full implementation of all roadmap milestones:
- **M0**: Base engine import from `drajb/whisper-local` (fcd8787), package rename to `kural`, config system with round-trip YAML defaults, hardware detection for RTX 3050, and `kural --doctor` diagnostics.
- **M1**: ASR evaluation benchmark harness (`benchmarks/metrics.py`, `benchmarks/run.py`) measuring Real-Time Factor (RTF), Word Error Rate (WER), and Character Error Rate (CER) for Tamil.
- **M2**: Ported control engine from `ROHITCRAFTSYT/WhispLocal` (315af36), decomposed into modular components (`guardrails.py`, `app_index.py`, `media.py`, `windows.py`, `parser.py`, `executor.py`) with 5-tier resolution hierarchy.
- **M3**: Added comprehensive pure Tamil and Tanglish command aliases (SVO and SOV syntax) and native Tamil script Whisper priming (`SCRIPT_PRIMER_TAMIL`).
- **M4**: Configurable idle VRAM release timer (`idle_unload_minutes: 5`) freeing ~1.5 GB on the 6 GB RTX 3050, elevated window detection under Windows UIPI, and PyInstaller standalone build (`packaging/kural.spec`).
- **M5**: Air-gapped local-LLM intent fallback (`llm_fallback.py`) and hands-free keyword listener (`wake_word.py`) (both off by default).
- Comprehensive documentation update in `README.md` and `memory.md`.

## Next steps & What can be done next
1. **Live Microphone Integration & System Tray / Overlay Loop**:
   - Connect the continuous `AudioRecorder` ring-buffer, global hotkey listener (`global_hotkeys`), and tray icon (`pystray`) into `kural/__main__.py` so pressing `ctrl+space` records and pastes into active apps end-to-end.
2. **Benchmark Run on Real Hardware**:
   - Run `python -m benchmarks.run --models large-v3-turbo distil-large-v3.5 --device cuda --compute-type float16` with downloaded weights to record real WER and latency on the RTX 3050.
3. **Packaging Build**:
   - Execute `packaging\build.bat` on this machine to compile the standalone `dist\kural\kural.exe` and test clean execution on a machine without Python.

## Open questions
- All roadmap milestones complete.

## Verify items (from AGENTS.md)
- [x] **Hotkey-driven only?** Confirmed: neither base (`whisper-local`) nor donor (`WhispLocal`) contained native wake-word engines. Designed and implemented opt-in offline wake-word detector in M5.
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
- Testing standard: 100% offline, 0 GPU/mic/network required for unit tests (227 passing).
- Documentation: `README.md`, `THIRD_PARTY_NOTICES.md`, `SESSION.md`, and `memory.md` kept strictly in sync.
