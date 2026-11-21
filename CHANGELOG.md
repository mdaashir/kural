# Changelog

All notable changes to Kural will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- A Next.js static-export marketing and documentation site prepared for GitHub Pages at `/kural/`, with verified v0.1.3 download links, product overview, user/developer docs, sitemap, and responsive navigation. Pages deployment is pending merge and repository Pages settings.
- Containerization for headless Whisper API: multi-stage Linux `Dockerfile` (non-root `kural` user, healthcheck, `ffmpeg`), `docker-compose.yml` (loopback-bound to `127.0.0.1:7777` for privacy), and GitHub Actions automated build/push workflow (`.github/workflows/docker.yml`) publishing to GitHub Container Registry (`ghcr.io/mdaashir/kural`).
- Optional `server` dependency extra in `pyproject.toml` containing `faster-whisper`, `soxr`, and `soundfile` for lightweight headless deployments without Windows desktop GUI/hotkey libraries.

### Changed
- Prepare `cmd-kural` 0.1.2 after the failed unpublished 0.1.1 release; the `v0.1.1` tag remains unchanged because it points to a pre-fix commit.
- Prepare `cmd-kural` 0.1.3 to fix installed `kural --version` and `kural.__version__`, which report stale 0.1.0/0.1.0-dev values in the published 0.1.2 package. The `kural` CLI and import package name remain unchanged.
- The v0.1.0 GitHub Release and its `kural` distribution wheel remain unchanged.
- Add a manually triggered, OIDC-only PyPI publishing workflow gated on package ownership, PyPI Trusted Publisher setup, the protected GitHub `pypi` environment, and `PUBLISH_PYPI=true`.

### Fixed
- Install uv 0.13.9 and Python 3.12 in the PyPI publish job before `uvx` metadata validation; add a parsed-workflow ordering regression test. Approved run `44851392430` failed before upload with exit 127.

### Notes
- `cmd-kural` 0.1.2 publication remains pending; its existing tag is unchanged. A matching pending PyPI publisher can create the project on first successful upload, but does not reserve the name.
- Install command after publication: `uv tool install --python 3.12 --from "cmd-kural[runtime,tray]" kural`. The installed command and Python import remain `kural`.

## [0.1.0] - 2026-11-20

### Added

#### Speech Engine & Hardware
- **GPU-Accelerated Inference:** Local Faster-Whisper engine running on NVIDIA CUDA `float16` with default `large-v3-turbo` model, targeting the NVIDIA RTX 3050 (6 GB VRAM).
- **CPU Fallback:** Automatic fallback to CPU `int8` with a visible user notification when no CUDA-capable GPU is detected.
- **Idle VRAM Unload:** Configurable timer (default 5 minutes) that transparently unloads the Whisper model from GPU memory during inactivity, freeing ~1.5 GB VRAM for other graphics applications, and reloads on the next dictation.
- **Bilingual Dictation:** Native-script Tamil (*தமிழ்*), English, and mixed Tanglish code-switching.
- **Indic Script Formatting:** Configurable native Tamil script output or Romanized phonetic Tanglish output via `SCRIPT_PRIMER_TAMIL` and `ROMAN_PRIMER_TAMIL`.
- **Whisper Mode:** Adaptive audio gain booster for quiet or whispered speech with 99.9th-percentile pop rejection and noise-floor protection.
- **Noise Suppression:** Optional spectral gating noise reduction via `noisereduce` to filter fan and HVAC hum.

#### Voice Control & Windows Automation
- **App Indexer:** Automatic indexing of Windows Start Menu shortcuts and Microsoft Store (UWP) apps with multi-tier fuzzy matching.
- **Bilingual Command Parser:** Grammar support for Subject-Verb-Object (*"open chrome"*, *"திற chrome"*) and Subject-Object-Verb (*"chrome திற"*, *"chrome open பண்ணு"*) phrasing.
- **Second-Pass Misheard Verb Recovery:** Recovers phonetically misheard leading verbs (*"oben chrome"* → *"open chrome"*).
- **Window Management:** Graceful application close via `WM_CLOSE`, window snapping (left, right, half), minimize, maximize, and restore.
- **Audio & Media Control:** Native Windows Core Audio endpoint volume adjustment, mute toggle, and media transport playback controls.
- **Window Elevation Safety (UIPI):** Win32 token elevation inspection that warns the user when the target window runs as Administrator instead of silently dropping input.
- **Command Hierarchy:** 5-tier resolution model: `commands.yaml` exact match → safety guardrails → built-in parser → fuzzy app index → not understood.

#### Safety Guardrails
- **Destructive Action Protection:** File deletion, partition formatting, and autonomous payments or bookings are strictly blocked by voice.
- **Protected Processes:** Prevents voice-closing system processes (`explorer.exe`, `taskmgr.exe`, `csrss.exe`).
- **Cancellable Power Actions:** System shutdown and restart require a delayed 60-second cancel window with explicit exit-code verification.

#### Dictation & Text Insertion
- **Push-to-Talk (PTT):** Hold-to-speak with instant finalization on key release.
- **Multi-Key Chord Matching:** Support for modifier combinations (e.g. `Ctrl+Alt`, `Ctrl+Windows`) with driver asymmetry resolution.
- **Mouse Flow:** Push-to-talk using mouse thumb buttons (`x1`, `x2`, middle click) with low-level event swallowing so browser Back/Forward is not triggered.
- **Double-Tap Hands-Free Lock:** Rapid double-tap (<450 ms) locks dictation in hands-free mode; tap once more to finish.
- **Instant Cancel Hotkey:** Press `Escape` (or configured shortcut) to instantly discard the recording buffer without transcribing or typing.
- **Hands-Free Voice Stop Phrases:** Say *"stop dictation"*, *"stop recording"*, *"முடி"*, *"நிறுத்து"*, or *"stop பண்ணு"* to automatically finalize hands-free recordings.
- **Flexible Delivery Methods:**
  - `paste` (default): copies text to clipboard and issues `Ctrl+V`, then restores prior clipboard.
  - `type`: direct Unicode keystroke injection via Win32 `SendInput` KEYEVENTF_UNICODE for paste-blocked applications (VMs, remote desktops, games).
  - `copy`: places text on the clipboard without sending keystrokes to the foreground window.
- **Clipboard History Retention:** Option to keep dictations in Windows Clipboard History (`Win+V`) instead of restoring prior clipboard state.
- **Return to App:** Automatically refocuses the originating application window before delivering text if a notification or alert stole focus during speech.
- **Caret-Aware Insertion Planner:** Win32 caret inspection that handles sentence capitalization, spacing after quotes/brackets, and mid-sentence continuation.
- **Flow Disfluency Stripper:** Automatic removal of verbal fillers (*"um"*, *"uh"*, duplicate false starts) and spoken punctuation translation (*"comma"*, *"period"*, *"புள்ளி"*, *"கமா"*).
- **In-Place Voice Editing:** Replaces selected or targeted words by voice (*"replace X with Y"*).
- **Text Transforms:** Developer casing tools (camelCase, snake_case, kebab-case, PascalCase, backticks, code blocks).
- **Notes Quick-Capture:** Direct Markdown note capture to Obsidian or daily journal vaults with YAML frontmatter.

#### User Interface & Desktop Integration
- **Soundwave Visual Overlay:** Click-through floating pill with 7 dynamic vertical harmonic bars showing live microphone volume.
- **Live Speech Streaming Preview:** Real-time interim partial words displayed inside the floating pill while speaking.
- **System Tray Icon:** Pystray menu with quick access to Settings, History, Cheat Sheet, Paste Last, Retry Last, and Incognito Mode.
- **Synthesized Audio Cues:** Pure-Python harmonic sine tones with smooth attack envelopes for start, stop, complete, and error events (zero audio files on disk).
- **Terminal Title State:** Dynamic ANSI OSC 0 terminal tab title animations (`[● Dictating]`, `[⏳ Processing]`, `[✔ Done]`).
- **Graphical Settings Dialog:** Tkinter dark-themed configuration window with live hotkey detection, audio settings, and delivery options.
- **Graphical History Browser:** Search-as-you-type history browser with BM25 full-text search and one-click copy.
- **Cheat Sheet Window:** Quick-reference dialog showing all shortcuts and bilingual voice commands.
- **Fallback Safety-Net Window:** Rescues unplaced or blocked dictations into a dark-themed modal with pre-selected text and instant copy.
- **Single-Instance Win32 Mutex:** Named mutex (`Local\Kural_SingleInstance`) preventing duplicate instances and offering graceful takeover.
- **Windows Autostart:** Optional startup on user login via Windows registry Run key with windowless `pythonw.exe` execution.

#### Privacy & Data Recovery
- **100% Air-Gapped Local Operation:** No telemetry, analytics, or cloud connections; the only network request is the initial one-time model download.
- **Incognito Mode:** One-click tray toggle that disables `history.jsonl` writes, adaptive vocabulary learning, DPAPI audio retention, and in-memory ledger storage; entering Incognito immediately purges prior takes.
- **Encrypted Audio Recovery (`LastTake`):** DPAPI-encrypted single-take raw audio recording on disk with 24-hour expiry and corruption resilience.
- **In-Memory Ledger:** Ephemeral memory store of the last dictation enabling *"paste last dictation"* across windows.
- **Redacted Diagnostic Bundler:** `kural --bundle-logs` creates a clean ZIP archive with automatic redaction of Windows usernames, paths, and sensitive secrets.

#### Offline File Transcription & Local API
- **CLI File Transcription:** `kural --transcribe <file> [--format {text,srt,json}] [--output <file>]` for offline audio file transcription. Supports WAV (8/16/24/32-bit PCM) and non-WAV formats via `soundfile`.
- **Local OpenAI-Compatible Server:** `kural --serve [--host 127.0.0.1] [--port 7777]` providing `GET /health`, `GET /v1/models`, and `POST /v1/audio/transcriptions` endpoints with multipart upload support, `response_format` validation (`json`, `text`), and `language=auto` detection.

#### Tooling & Distribution
- **Complete Offline Test Suite:** 579 unit tests running completely offline without GPU, microphone, model download, or network.
- **GitHub Actions CI Pipeline (`ci.yml`):** Automated PR and push validation running `ruff check`, `ruff format --check`, offline `pytest`, `twine check --strict`, Python package builds, and standalone desktop bundle verification.
- **GitHub Actions Release Pipeline (`release.yml`):** Automated release workflow triggered on version tags (`v*.*.*`) or manual dispatch, generating `kural-windows-x64-setup.exe`, `kural-windows-x64.zip`, Python wheels, source distributions, and cryptographic `SHA256SUMS`.
- **Windows Setup Installer (`kural.iss`):** Inno Setup 6 per-user lowest-privilege Windows installer.
- **Standalone Portable Bundle:** PyInstaller distribution (`dist\kural\kural.exe`) requiring no Python installation.
