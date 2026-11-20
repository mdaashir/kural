# Memory — Kural Full Roadmap Implementation (M0 - M5)

Last updated: 2026-11-21 05:08 IST

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

## v0.1.0 release & distribution — 2026-11-20

- PR #95 merged and authorized annotated `v0.1.0` tag pushed from main commit `abc4a018`.
- GitHub Release: https://github.com/mdaashir/kural/releases/tag/v0.1.0
- Release workflow run `44782776964` passed validation, test, packages, desktop, and GitHub release jobs.
- Published assets (Windows setup installer, portable ZIP, Python wheel, source archive, `SHA256SUMS`) were downloaded and independently checksum-verified.
- PyPI publishing remains disabled; no package published. Existing PyPI project `kural` belongs to another owner.

## cmd-kural PyPI release recovery — 2026-11-21

- PR #97 prepared distribution `cmd-kural` version 0.1.1; Python import and CLI remain `kural`.
- PR #98 corrected PEP 427 underscore normalization for wheel/sdist names; CI run `44835854722` passed all test/package/desktop jobs.
- Existing tag `v0.1.1` points to pre-PR #98 commit `f82ac4d`. Release run `44832574129` failed artifact validation before GitHub Release creation or PyPI publication. Do not move or force-update this tag.
- Safe recovery requires a new version/tag (proposed 0.1.2): PR bumps `pyproject.toml`, uv.lock, changelog/docs; after merge create a new annotated tag from main.
- PyPI `cmd-kural` returned 404 at last check, but is not reserved. Pending publisher screenshot shows owner/repo/workflow/environment configured; GitHub `pypi` environment exists but has no protection rules. `PUBLISH_PYPI` remains unset and no PyPI upload has occurred.
- Trusted publisher values: project `cmd-kural`, owner `mdaashir`, repository `kural`, workflow `publish-pypi.yml`, environment `pypi`; OIDC only, no API token.

## Current state

- The historical M0–M5 roadmap is complete; post-M5 features, desktop builds, and CI/CD pipelines are merged on `main`.
- Current `main` at handoff: `f52e5b5`; current GitHub Release is v0.1.0. Next intended distribution is `cmd-kural` 0.1.2 after a version-bump PR.
- `.github/workflows/ci.yml` and `build.yml` validate code, package wheel/sdist, smoke-test `uv tool`, and build/smoke-test Windows portable bundle and installer.
- `.github/workflows/release.yml` publishes desktop/GitHub assets; separate manual `.github/workflows/publish-pypi.yml` is gated by `PUBLISH_PYPI == 'true'`.
- Last local verification after PR #98: 582 tests pass. Do not retry v0.1.1 release as its tag commit is not current-main ancestry after the artifact fix.
- No v0.1.2 release, PyPI upload, GHCR image, or Pages deployment has occurred.

## Next session starts with

- Confirm PR #98 post-merge CI on main; prepare one version-bump PR to `cmd-kural` 0.1.2 and update lock/changelog/docs.
- After review/merge, tag v0.1.2 from main and verify GitHub Release artifacts/checksums.
- Only after the user verifies package ownership/trusted publisher and adds protection to GitHub `pypi` environment, with explicit confirmation, set `PUBLISH_PYPI=true` and manually dispatch `publish-pypi.yml`.
- Then handle separate GHCR API image and Next.js GitHub Pages site PRs.

## Open questions

- Confirm account ownership of PyPI `cmd-kural`; 404/pending publisher does not reserve it.
- Confirm GitHub `pypi` environment protection rules before enabling publishing.
- The local transcription API supports only `json` and `text`; SRT response output is not implemented.
- Live model inference, full microphone/UI workflow, and real client-disconnect timing require hardware/manual verification.
