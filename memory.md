# Memory — Kural Full Roadmap Implementation (M0 - M5)

Last updated: 2026-11-20 15:47 IST

## What was built

Implemented the complete Kural architecture across 9 merged Pull Requests:
1. **Repository Skeleton & Setup (`PR #1`)**: `pyproject.toml` (hatchling backend), `.python-version` (3.12), `LICENSE` (MIT), `THIRD_PARTY_NOTICES.md`, and clean package stubs (`kural/engine/`, `kural/control/`, `kural/config/`, `kural/ui/`).
2. **Base Engine Port (`PR #2`)**: Ported audio & speech recognition engine from `drajb/whisper-local` (commit `fcd8787`): `audio_recorder.py`, `dictation_cleanup.py`, `dictation_languages.py`, `model_registry.py`, `model_transfer.py`, `streaming_delivery.py`, `streaming_manager.py`, `streaming_recognizer.py`, `voice_activity_detection.py`, and `whisper_engine.py` (with defaults targeting NVIDIA RTX 3050 CUDA float16 `large-v3-turbo`).
3. **Configuration & Diagnostics (`PR #3`)**: Ported `config_manager.py` (defaults layering under `%APPDATA%\kural\user_settings.yaml`, hot-reload, validation), `defaults_merge.py`, `config.defaults.yaml`, `commands.defaults.yaml`, `hardware_detection.py` (GPU & CUDA DLL probe), and `doctor.py` CLI (`kural --doctor`).
4. **ASR Benchmark Harness (`PR #4`)**: Built `benchmarks/metrics.py` (Levenshtein distance, WER, character error rate CER for Tamil), `benchmarks/datasets.py` (manifest & synthetic 16 kHz WAV generator), and `benchmarks/run.py` (CLI runner with Markdown/JSON comparison reports).
5. **Control Engine Foundation (`PR #5`)**: Ported from `ROHITCRAFTSYT/WhispLocal` (commit `315af36`): `guardrails.py` (file deletion/autonomous transaction blocker, protected processes, 60s cancellable shutdown), `app_index.py` (Start Menu + UWP Store app indexer, 202 apps indexed live on Win 11, fuzzy matching), and `media.py` (Windows Core Audio `IAudioEndpointVolume` via ctypes).
6. **Window Management & Command Resolution (`PR #6`)**: Built `windows.py` (`EnumWindows`, `SwitchToThisWindow`, graceful `WM_CLOSE`, snap/minimize), `parser.py` (pure intent parser with second-pass misheard verb recovery), and `executor.py` implementing the 5-tier resolution hierarchy (`commands.yaml` exact -> guardrails -> built-in parser -> app index -> not understood).
7. **Tamil & Tanglish Voice Commands (`PR #7`)**: Extended `parser.py` with SOV (*"chrome திற"*, *"notepad open பண்ணு"*) and SVO (*"திற chrome"*) grammar, Tamil volume/media commands, Tamil app aliases (*"குரோம்"*, *"நோட்பேடு"*), pre-configured defaults in `commands.defaults.yaml`, and injected `SCRIPT_PRIMER_TAMIL` in `WhisperEngine` to steer Whisper to Tamil Unicode output.
8. **Ops, Idle VRAM Unload & Packaging (`PR #8`)**: Added configurable idle VRAM release timer (`idle_unload_minutes: 5`) freeing ~1.5 GB on the 6 GB RTX 3050 during inactivity, elevated window detection (`is_window_elevated`) warning on Windows UIPI keystroke drops, and standalone PyInstaller specification (`packaging/kural.spec` & `build.bat`).
9. **Optional Capabilities (`PR #9`)**: Built `llm_fallback.py` (local-LLM GGUF/ONNX intent fallback, air-gapped, re-parsed via deterministic regexes) and `wake_word.py` (offline keyword activation listener for *"Hey Kural"* / *"குரல்"*).

## Decisions made

- **Architecture separation**: Clean decoupling between `engine` (speech/audio), `control` (automation/OS actions), `config` (settings), and `benchmarks`.
- **Hardware defaults**: RTX 3050 Laptop GPU targeted with `large-v3-turbo` in CUDA `float16`.
- **Idle VRAM unload**: Configurable timer (default 5 min) unloads model from VRAM (`del self.model; gc.collect()`) and transparently reloads on the next dictation without app restart.
- **Strict safety hierarchy**: User commands exact match -> Guardrails check -> Built-in parser -> Fuzzy app index -> Optional LLM fallback -> Not understood. Destructive file operations and financial transactions are completely blocked by voice.
- **Dual-language parser**: Supports English, pure Tamil, and colloquial Tanglish code-switching in both Subject-Object-Verb and Verb-Object syntax.
- **Offline test rule**: Unit tests are designed to run without GPU, mic, model download, or network.

## Problems solved

- **Elevated Windows UIPI block**: Standard user apps cannot inject keystrokes into Administrator windows; resolved by querying token elevation (`TokenElevation` via `OpenProcessToken`) and providing clear user warnings.
- **Whisper Tamil script degradation**: Whisper occasionally falls back to phonetic Latin transliteration when transcribing Tamil; resolved by automatically injecting `SCRIPT_PRIMER_TAMIL` into `initial_prompt`.
- **Upstream 1,900-line monolith**: Decomposed into 6 single-responsibility modules under 300 lines each (`app_index`, `guardrails`, `media`, `windows`, `parser`, `executor`).
- **GPU VRAM starvation**: Idle VRAM unload prevents running out of VRAM when other graphics applications or games run alongside Kural.

## Current state

- The historical M0–M5 roadmap above is complete; desktop/runtime features and targeted fixes have continued through PR #88.
- PR #88 is merged into `main`; current recovery-data fix is on `fix/recovery-corrupt-last-take`.
- The current full suite has 571 passing tests; `ruff check .` and `ruff format --check .` pass.
- Local API supports exact routes `GET /health`, `GET /v1/models`, and `POST /v1/audio/transcriptions`; supported response formats are JSON and plain text. Multipart parsing uses the stdlib MIME parser, enforces Content-Length and a 500 MiB cap, and preserves boundary-like bytes in binary files.
- Incognito disables history/adaptive/audio retention and in-memory ledger/Paste Last retention; entering the mode clears the existing take and ledger.
- Local GPU inference and live microphone/UI behavior have not been re-verified in this iteration.

## Next session starts with

- Finish verification and open the PR for `fix/recovery-corrupt-last-take`.
- After that PR is reviewed and merged, continue one focused implementation issue at a time, reproducing it before editing and updating all relevant docs each iteration.

## Open questions

- The local transcription API intentionally supports only `json` and `text`; SRT response output is not implemented.
- Live model inference, full microphone/UI workflows, and real client-disconnect timing still need hardware/manual verification when available.
- The recovery fix stubs decryption for malformed-plaintext testing; Windows DPAPI corruption behavior is not tested on hardware.
