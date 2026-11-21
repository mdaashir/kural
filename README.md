<meta name="description" content="Kural is a local-first Windows speech-to-text and voice typing app with GPU-accelerated Whisper, voice commands, and support for English, Tamil, and Tanglish. No cloud transcription.">
<meta name="keywords" content="offline speech to text, Windows voice typing, local Whisper, Tamil speech recognition, Tanglish voice commands, GPU transcription, privacy-first dictation">

# Kural (குரல்)

> Offline speech-to-text, voice typing, and voice commands for Windows. Powered by local GPU-accelerated Whisper; supports English, Tamil, and Tanglish without cloud transcription.

**Latest release: [Kural v0.1.0](https://github.com/mdaashir/kural/releases/tag/v0.1.0)** — download the [Windows installer](https://github.com/mdaashir/kural/releases/download/v0.1.0/kural-windows-x64-setup.exe), [portable Windows bundle](https://github.com/mdaashir/kural/releases/download/v0.1.0/kural-windows-x64.zip), or [Python wheel](https://github.com/mdaashir/kural/releases/download/v0.1.0/kural-0.1.0-py3-none-any.whl). Verify downloads with the release [SHA256SUMS](https://github.com/mdaashir/kural/releases/download/v0.1.0/SHA256SUMS).

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Platform: Windows 11](https://img.shields.io/badge/platform-Windows%2011-0078D6.svg)](https://www.microsoft.com/windows)
[![CUDA: RTX 3050](https://img.shields.io/badge/CUDA-RTX%203050%206GB-76B900.svg)](https://developer.nvidia.com/cuda-zone)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![CI](https://github.com/mdaashir/kural/actions/workflows/ci.yml/badge.svg)](https://github.com/mdaashir/kural/actions/workflows/ci.yml)
[![Tests: 589](https://img.shields.io/badge/tests-589%20passing-brightgreen.svg)](tests/)

Kural merges two MIT-licensed upstream projects into one cohesive desktop voice assistant:
the **GPU speech engine** from `drajb/whisper-local` with the **deep voice-control engine**
from `ROHITCRAFTSYT/WhispLocal` — extended with Tamil/Tanglish support, Wispr Flow-style UX,
and Windows-native privacy features.

---

## Key Highlights

- **Bilingual Voice Typing & Control:** Native script Tamil (*தமிழ்*), English, and code-switched Tanglish (*"chrome open பண்ணு"*, *"notepad திற"*).
- **GPU Accelerated:** `large-v3-turbo` on CUDA `float16` targeting the NVIDIA RTX 3050 (6 GB). CPU `int8` fallback with a visible warning.
- **Idle VRAM Unload:** Automatically releases GPU memory after configurable inactivity (default: 5 min), transparently reloading on next dictation — freeing ~1.5 GB on the RTX 3050 for other apps.
- **Deep Windows Voice Control:**
  - Launch & switch apps indexed from the Windows Start Menu and Microsoft Store.
  - Multi-tier fuzzy matching and second-pass misheard-verb recovery (*"oben chrome"* → *"open chrome"*).
  - Graceful window closing (`WM_CLOSE`), window snapping, minimizing, and maximizing.
  - System volume & media transport controls via Windows Core Audio.
- **Strict Guardrails:** Blocks file deletion, partition formatting, and autonomous payments. Delayed 60 s cancellable window for shutdown/restart.
- **Elevated Window Detection:** Detects UIPI-blocked Administrator windows and notifies the user instead of silently dropping synthetic input.
- **Wispr Flow-style UX:**
  - Animated 7-bar soundwave equalizer pill with live mic level during recording.
  - Live partial speech streaming preview in the pill while Whisper processes.
  - Soft synthesized bell-chime audio cues (no audio files on disk).
  - Push-to-talk via keyboard hotkey, multi-key chord (`ctrl+windows`, `ctrl+alt`), or mouse thumb button (Mouse Flow).
- **Privacy-First:**
  - Zero runtime telemetry or cloud calls.
  - **Incognito Mode:** disables transcript history, adaptive learning, audio retention, and in-memory Paste Last retention while active. Entering Incognito clears any prior retained take and ledger text.
  - DPAPI-encrypted audio retention for one-click retry and paste-last recovery when Incognito is off.
  - Transcript text is never logged at INFO level.
- **Never-Lose-A-Dictation:** Paste last dictation and retry last recording directly from the system tray.
- **Text Delivery Choice:** Clipboard paste (`paste` / Ctrl+V), direct SendInput Unicode keystrokes (`type`) for paste-blocked apps, or Copy Only (`copy`) to clipboard without disturbing foreground focus (Hex-inspired).
- **100% Local:** Air-gapped text pipeline. The only network call is the one-time model download.

---

## Architecture Overview

```
kural/
├── engine/                     # Audio capture, faster-whisper inference, VRAM lifecycle
│   ├── whisper_engine.py         faster-whisper CUDA float16 + idle VRAM unload timer
│   ├── file_transcriber.py       Offline audio file transcription CLI (Hex-inspired)
│   ├── audio_recorder.py         Ring-buffer continuous WASAPI capture with resampling
│   ├── audio_ducking.py          Automatic playback volume ducking while dictating (Hex-inspired)
│   ├── stop_phrase.py            Hands-free voice stop phrase detection & stripping (Hex-inspired)
│   ├── audio_feedback.py         Soft synthesized bell-chime audio cues (no WAV files)
│   ├── audio_gain.py             Whisper Mode adaptive booster for quiet/whispered speech
│   ├── cues.py                   Pure-Python sine harmonic WAV synthesis (stdlib only)
│   ├── streaming.py              Real-time partial speech preview in the overlay pill
│   ├── hardware_detection.py     GPU & CUDA DLL diagnostics (cuBLAS, cuDNN)
│   ├── voice_activity_detection.py  TEN VAD silence detector
│   ├── wake_word.py              Optional offline keyword listener (behind config flag)
│   ├── model_registry.py         Local & HuggingFace cache management
│   ├── flow_formatting.py        Disfluency stripper & spoken punctuation engine
│   ├── dictation_cleanup.py      Text normalization pipeline
│   ├── dictation_languages.py    EN/TA language and prompt configuration
│   ├── snippets.py               Inline text snippet expansion (${date}, ${clipboard})
│   ├── dictionary.py             Custom hotword dictionary (--dict-add/list/remove)
│   ├── adaptive.py               On-disk adaptive vocabulary learning (adaptive.json)
│   ├── history.py                JSONL history logger with BM25 full-text search
│   ├── recovery.py               DPAPI-encrypted LastTake audio retention & Ledger
│   ├── notes.py                  Voice-capture to Obsidian/Markdown daily journal
│   ├── server.py                 Local OpenAI-compatible speech API (127.0.0.1)
│   └── utils.py                  %APPDATA% path helpers & version reader
│
├── control/                    # Voice-control brain, automation, and OS integration
│   ├── executor.py               5-tier command resolution: exact → built-in → fuzzy → LLM → error
│   ├── parser.py                 Pure intent parser (SVO/SOV, English, Tamil, Tanglish)
│   ├── tamil_parser.py           Native Tamil & Tanglish alias matching
│   ├── app_index.py              Start Menu & Store app indexer with fuzzy matching
│   ├── app_rules.py              Per-app contextual delivery (verbatim, formal, casual…)
│   ├── planner.py                Caret-aware continuation layout planner
│   ├── windows.py                Window info, snap, focus; Unicode SendInput injection
│   ├── chords.py                 Multi-key push-to-talk chord tracker (ChordMatcher)
│   ├── mouse.py                  Win32 WH_MOUSE_LL mouse-button push-to-talk (Mouse Flow)
│   ├── media.py                  Windows Core Audio volume & media transport
│   ├── guardrails.py             Safety allowlist & destructive action blocker
│   ├── llm_fallback.py           Air-gapped local-LLM intent fallback (GGUF/ONNX)
│   ├── autostart.py              Windows Run registry startup integration
│   └── elevation.py              UIPI elevated-window detection
│
├── config/                     # Layered configuration & defaults
│   ├── config_manager.py         %APPDATA%\kural overlay + schema validation + auto-heal
│   ├── configcheck.py            Key-by-key schema validator with typed bounds
│   ├── config.defaults.yaml      Engine & control defaults (all sections)
│   └── commands.defaults.yaml    Bilingual voice command triggers
│
├── ui/                         # Desktop visual surface
│   ├── overlay.py                Animated 7-bar soundwave equalizer pill (Tkinter)
│   ├── tray.py                   Windows notification area icon with recovery actions
│   ├── settings_window.py        Graphical settings dialog (tabbed, Tkinter)
│   ├── history_window.py         Dark-theme history browser with live BM25 search
│   └── cheat_sheet.py            Shortcuts & commands quick-reference dialog
│
├── doctor.py                   # `kural --doctor` diagnostic health check
├── runtime.py                  # Main daemon: state machine, hotkeys, audio loop
├── benchmarks/                 # ASR harness: WER, Tamil CER, RTF on GPU
└── packaging/                  # Standalone PyInstaller build (kural.exe)
```

---

## Getting Started

### Prerequisites

- **OS:** Windows 11 (AMD64)
- **Python:** 3.12+ (managed with `uv` or system Python)
- **GPU (Recommended):** NVIDIA RTX 3050 or any CUDA 12-compatible GPU with latest drivers

### Installation

```powershell
# Clone the repository
git clone https://github.com/mdaashir/kural.git
cd kural

# Create environment and install dependencies
uv venv
.\.venv\Scripts\activate

# Core package (library + diagnostics)
uv pip install -e .

# Full desktop runtime (dictation engine, audio, hotkeys, UI)
uv pip install -e ".[runtime]"

# Optional extras: tray icon, voice activity detection
uv pip install -e ".[tray,vad]"
```

### Reproducible builds and release artifacts

Contributors and CI use the committed `uv.lock` with Python 3.12:

```powershell
uv sync --locked --python 3.12 --extra dev --extra runtime --extra tray
uv run --no-sync ruff check .
uv run --no-sync ruff format --check .
uv run --no-sync pytest -m "not gpu and not mic"
uv build --out-dir dist/packages
uv run --no-sync python packaging/smoke.py --packages dist/packages
packaging\build.bat
```

CI reuses the same verification jobs for PRs and tag releases. It uploads a wheel,
sdist, and full Windows x64 desktop ZIP (runtime and tray dependencies included;
optional TEN VAD, models and NVIDIA CUDA libraries are not bundled). Package checks
install both archives with `uv tool install` into temporary tool environments;
the desktop ZIP is extracted and checked outside the checkout. Checks cover CLI,
packaged defaults, and desktop dependency imports, not live audio/GPU/UI behavior.
`--doctor` and `--selftest` remain manual hardware diagnostics, not CI gates.

To install a downloaded wheel as a desktop tool without cloning the repository:

```powershell
uv tool install --python 3.12 "C:\path\to\kural-0.1.0-py3-none-any.whl[runtime,tray]"
kural --version
```

The next PyPI distribution is `cmd-kural`; the import package and executable remain `kural`. **The published 0.1.2 package reports a stale `kural --version` value. Version 0.1.3 is being prepared to correct package and CLI version reporting; avoid 0.1.2 if checking the reported version.** After 0.1.3 is published, install it as a CLI tool:

```powershell
uv tool install --python 3.12 --from "cmd-kural[runtime,tray]==0.1.3" kural
kural --version
```

Until then, use the [v0.1.0 GitHub Release wheel](https://github.com/mdaashir/kural/releases/download/v0.1.0/kural-0.1.0-py3-none-any.whl). The unrelated `kural` PyPI project must not be used. A matching pending Trusted Publisher can create `cmd-kural` on first successful upload; it does not reserve the name.

GitHub Releases run only when an existing `v<project.version>` tag is pushed; the tag must
match `pyproject.toml` exactly. Verified desktop and Python artifacts are attached there.
PyPI publishing uses the separate manual `.github/workflows/publish-pypi.yml` workflow and
is disabled unless repository variable `PUBLISH_PYPI=true`. Before publishing, configure
the exact trusted publisher (pending publisher for a new project) and protected GitHub
`pypi` environment, and verify their settings. It uses OIDC only; no API token is used,
and pull requests never publish. See [RELEASE.md](RELEASE.md) for exact PyPI setup steps.

### Running Kural

```powershell
# Start the live dictation daemon
python -m kural
```

```
=======================================================
   Kural 0.1.0 — Ready
=======================================================
   [Ctrl+Space]         Dictation Mode (speech → active cursor)
   [Ctrl+Shift+Space]   Command Mode (voice control)
   Model: large-v3-turbo (cuda)
   Press Ctrl+C to exit.
```

An animated soundwave equalizer pill appears at the screen edge while you speak, showing a live
mic level. The pill is click-through so it never blocks your mouse. A soft bell chime plays when
recording starts and when text is delivered.

### System Health Check

Verify hardware, CUDA libraries, audio setup, and configuration:

```powershell
python -m kural --doctor
```

Expected output:

```
Kural — Doctor Diagnostics
============================

Runtime
  [OK]   Python version    3.12.x (target 3.12+)
  [i]    Platform          Windows 11 (AMD64)
  [OK]   Kural version     0.1.0

Hardware & GPU (Target: NVIDIA RTX 3050)
  [OK]   Detected GPU      NVIDIA GeForce RTX 3050 (nvidia)
  [OK]   CUDA runtime      v12.x
  [OK]   CUDA inference libraries   cuBLAS & cuDNN available

Dependencies
  [OK]   numpy             installed
  [OK]   faster_whisper    v1.x
  ...

Configuration
  [OK]   Config directory  C:\Users\<you>\AppData\Roaming\kural
  [OK]   Config integrity  All settings valid
  [i]    Selected model    large-v3-turbo on cuda (float16)

Audio & Microphone
  [OK]   Default microphone   <Microphone Name> (48000 Hz)
  [OK]   Voice activity detection   TEN VAD ready

Model Cache
  [OK]   Idle VRAM unload   5 min timeout (frees GPU memory)
  [OK]   Model 'large-v3-turbo' cached
```

---

## Usage

### Dictation

| Mode | Hotkey | Action |
|---|---|---|
| Dictation | `Ctrl+Space` | Toggle (or hold in push-to-talk mode) |
| Command | `Ctrl+Shift+Space` | Voice control |
| Cancel | `Escape` | Discard active recording without transcribing or delivering it |
| Paste Last | Tray menu / `Ctrl+Alt+V` | Re-type last non-Incognito dictation at the active cursor |
| Retry Last | Tray menu | Re-transcribe the retained audio take when Incognito is off |
| Incognito | Tray menu | Disable history, learning, audio retention, and ledger/Paste Last retention |

**Push-to-Talk variants:**
- **Keyboard hotkey** – hold `Ctrl+Space` while speaking
- **Multi-key chord** – configure any combo like `ctrl+windows` or `ctrl+alt` via settings
- **Mouse Flow** – hold thumb button (`x1`, `x2`, or middle click) while speaking; button's default Windows action (browser Back/Forward) is suppressed during dictation

**Double-tap to lock hands-free:** tap the hotkey twice quickly (<450 ms) to stay in hands-free mode — tap once more to stop.

**Text delivery methods:**
- `paste` (default): copies to clipboard and sends `Ctrl+V`, then restores the prior clipboard.
- `type`: injects each character directly via Win32 `SendInput` KEYEVENTF_UNICODE — works in paste-blocked apps such as VMs, remote desktops, and games.
- `copy`: copies the formatted transcript to the clipboard without sending keystrokes to the foreground app.

### Voice Commands

Kural recognizes commands in English, formal Tamil, and colloquial Tanglish:

| Action | English | Tamil | Tanglish |
|---|---|---|---|
| **Launch App** | *"open chrome"* | *"திற குரோம்"* / *"குரோம் திற"* | *"chrome open பண்ணு"* |
| **Close App** | *"close notepad"* | *"மூடு நோட்பேடு"* | *"notepad close பண்ணு"* |
| **Switch Window** | *"switch to edge"* | *"எட்ஜ்-க்கு போ"* | *"edge-க்கு மாற்று"* |
| **Volume Up** | *"volume up"* | *"சத்தம் ஏற்று"* | *"sound ஏத்து"* |
| **Volume Down** | *"volume down"* | *"சத்தம் குறை"* | *"sound குறை"* |
| **Mute Audio** | *"mute"* | *"ஒலியை நிறுத்து"* | *"மியூட் பண்ணு"* |
| **Media Play/Pause** | *"play"* / *"pause"* | *"பாடலை இயக்கு"* | *"play பண்ணு"* |
| **Window Snap** | *"snap left"* | *"இடதுபக்கம் மாற்று"* | *"snap left பண்ணு"* |
| **Show Desktop** | *"show desktop"* | *"டெஸ்க்டாப் காட்டு"* | *"desktop காட்டு"* |
| **Web Search** | *"search for python"* | *"பைதான் பற்றி தேடு"* | *"python தேடு"* |
| **YouTube Search** | *"search lofi on youtube"* | *"ரஜினி பாடல் யூடியூபில் தேடு"* | *"lofi youtube-ல தேடு"* |

### Smart Text Features

- **Disfluency cleaning:** removes *um*, *uh*, false-start duplicates before delivery.
- **Spoken punctuation:** *"full stop"* → `.`, *"புள்ளி"* → `.`
- **Voice rewrites:** *"make it a bullet list"*, *"title case"*, *"camelCase"*, *"snake_case"*
- **Voice editing:** *"replace error with issue"*, *"sort lines"*, code formatting transforms
- **Snippet expansion:** `${date}`, `${time}`, `${clipboard}` variables; `mode: anywhere` (default) expands inline, while `mode: alone` expands only when the full normalized dictation matches the trigger
- **Custom dictionary:** `kural --dict-add "Aashir"` — hotwords preserved during transcription
- **Adaptive vocabulary:** corrections and context learned on-disk session by session
- **Whisper Mode:** adaptive gain boost for quiet or whispered speech (99.9th percentile pop rejection)
- **Output Audio Ducking:** automatically lowers music/video playback volume while speaking so speakers don't bleed into the mic (Hex-inspired)
- **Instant Cancel Hotkey (`Escape`):** aborts dictation or voice control immediately and discards audio buffer without typing or logging (Hex-inspired)
- **Voice Stop Phrase:** say *"stop dictation"* or *"முடி"* / *"stop பண்ணு"* to automatically finalize hands-free dictation without pressing hotkeys (Hex-inspired)
- **Windows Clipboard History Retention:** optionally keep dictations in Windows Clipboard History (`Win+V`) instead of restoring prior clipboard (Hex-inspired)
- **Return to App:** attempts to refocus the original window before applying its app formatting/suppression rule; if Kural cannot confirm it is foreground, paste/type is withheld and the transcript is offered in the fallback window (Hex-inspired).

### Offline Audio File Transcription (`--transcribe`)

Inspired by [`anomalyco/hex`](https://github.com/anomalyco/hex), Kural can transcribe recorded audio files directly from the command line on your local GPU without running the background live dictation daemon:

```powershell
# Plain text transcription to stdout
python -m kural --transcribe meeting.wav

# Transcribe Tamil voice note and save SubRip (.srt) subtitles
python -m kural --transcribe recording.wav --format srt --output subtitles.srt

# Structured JSON export with timestamps and segments
python -m kural --transcribe audio.wav --format json --output transcript.json
```

### Local OpenAI-Compatible Transcription API

Kural can serve transcription requests locally on `127.0.0.1` using the configured Whisper model:

```powershell
# Start the local API server (default port 7777)
python -m kural --serve
```

Available endpoints:

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Local server health check |
| `GET` | `/v1/models` | OpenAI-compatible model list |
| `POST` | `/v1/audio/transcriptions` | Multipart audio transcription |

The POST endpoint requires a multipart `file` field. Optional fields include `language`, `prompt`, and `response_format`. Response formats are `json` (default, `{"text":"..."}`) and `text`; other values are rejected with HTTP 400. Malformed or incomplete multipart requests and undecodable audio return HTTP 400; transcription failures return HTTP 500 with a JSON error. Audio is decoded to mono 16 kHz; `soundfile` handles supported audio formats when installed, with standard PCM WAV fallback support for 16-, 24-, and 32-bit WAV. Upload bodies are limited to 500 MiB, and truncated bodies or malformed multipart framing are rejected.

```powershell
curl.exe -X POST http://127.0.0.1:7777/v1/audio/transcriptions `
  -F "file=@meeting.wav" `
  -F "language=ta" `
  -F "response_format=json"
```

#### Running via Docker / Docker Compose

The headless Whisper transcription server is also available as a container image published to GitHub Container Registry (`ghcr.io/mdaashir/kural`):

```bash
# Launch with Docker Compose (ports bound strictly to 127.0.0.1 for local privacy)
docker compose up -d

# Verify liveness
curl http://127.0.0.1:7777/health
```

> **Security Note:** The transcription API does not include authentication. It must remain bound to loopback (`127.0.0.1`) and never exposed directly to public networks without an authenticating reverse proxy.

### Benchmarks

Run the ASR benchmark harness to measure latency (RTF) and error rates (WER, Tamil CER):

```powershell
python -m benchmarks.run --models large-v3-turbo --device cuda --compute-type float16
```

### Building Packages and Standalone Executable

#### 1. Python Package Distributions (Wheel & sdist)

```powershell
uv build
```
Outputs: `dist/kural-0.1.0-py3-none-any.whl` and `dist/kural-0.1.0.tar.gz`.

#### 2. Standalone Windows Desktop App & Setup Installer

```cmd
packaging\build.bat
```
Output:
- `dist\kural\kural.exe` — a self-contained Windows application bundle with bundled configurations and no Python runtime installation required.
- `dist\kural-windows-x64.zip` — portable archive ready to unzip and run anywhere.
- `dist\kural-windows-x64-setup.exe` — per-user setup wizard installer (built with Inno Setup, lowest privileges, no admin rights required).

#### 3. Automated CI / CD & Releases

- **Continuous Integration (`.github/workflows/ci.yml`):** Runs on every push and pull request to `main`. Checks Ruff formatting, lints the codebase, executes all 579 offline unit tests, verifies package metadata (`twine check`), builds wheel/sdist distributions with smoke tests outside the repo, compiles the standalone desktop bundle, and smoke-tests both the portable `kural.exe` and silent installer.
- **Release Automation (`.github/workflows/release.yml`):** Triggered on version tags (`v*.*.*`) or via manual dispatch with a validated existing tag. Validates tag ancestry against `main`, executes the verified build pipeline, verifies the complete artifact set, generates cryptographically verified `SHA256SUMS`, creates an official GitHub Release with all binary assets attached, and optionally publishes to PyPI when trusted publishing is enabled. See [RELEASE.md](RELEASE.md) for maintainer procedures and [CHANGELOG.md](CHANGELOG.md) for full version history.

---

## Running Tests

All unit tests run 100% offline — no microphone, GPU, or network download required:

```powershell
# Run the complete offline test suite
pytest tests/ -q

# Code style and format checks
ruff check .
ruff format --check .
```

---

## Configuration

User settings live in `%APPDATA%\kural\user_settings.yaml`. Key sections:

| Section | Key | Default | Notes |
|---|---|---|---|
| `whisper` | `model` | `large-v3-turbo` | Whisper model variant |
| `whisper` | `device` | `cuda` | `cuda` or `cpu` |
| `whisper` | `idle_unload_minutes` | `5` | 0 = never unload |
| `hotkey` | `recording_hotkey` | `ctrl+space` | Dictation toggle |
| `hotkey` | `command_hotkey` | `ctrl+shift+space` | Command toggle |
| `hotkey` | `mouse_button` | `` (disabled) | `x1`, `x2`, `both`, `middle` |
| `hotkey` | `recording_mode` | `toggle` | `toggle` or `push_to_talk` |
| `clipboard` | `delivery_method` | `paste` | `paste` or `type` |
| `audio` → `whisper_mode` | `enabled` | `true` | Quiet speech boost |
| `overlay` | `position` | `bottom-center` | Pill position |

All settings can be changed via the **Settings** dialog (tray → Settings...) without editing YAML directly.

---

## Privacy & Safety

| Guarantee | Detail |
|---|---|
| **No telemetry** | Zero runtime network calls; only the one-time model download |
| **Transcript privacy** | Transcribed text is never logged at INFO level or transmitted anywhere |
| **Incognito Mode** | Disables history.jsonl writes, adaptive learning, DPAPI audio retention, and in-memory ledger/Paste Last retention; entering Incognito clears the prior take and ledger |
| **Audio retention** | DPAPI-encrypted, single take, 24 h expiry, wiped in Incognito |
| **Destructive action block** | File deletion, partition format, purchases blocked; shutdown/restart need 60 s cancel window |
| **Elevated window UIPI** | Detects and warns when target app runs as Administrator instead of silently failing |

---

## Attribution & Licenses

Kural is open-source under the [MIT License](LICENSE). It merges and adapts components from:
- **`drajb/whisper-local`** (fork of Pin Wang's `whisper-key-local`) — GPU engine, onboarding, doctor, settings
- **`ROHITCRAFTSYT/WhispLocal`** (by Rohit Burani) — voice-control engine, app index, fuzzy matching, guardrails, adaptive learning, recovery
- **`anomalyco/hex`** (by Christopher Langton) — audio ducking, file transcription CLI, stop phrases, cancel shortcuts, window focus return, clipboard retention

All upstream copyright lines are preserved in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
