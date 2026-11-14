# Kural (குரல்)

> Local-first voice typing + voice control for Windows. English and Tamil. GPU-accelerated Whisper, no cloud.

[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/)
[![Platform: Windows 11](https://img.shields.io/badge/platform-Windows%2011-0078D6.svg)](https://www.microsoft.com/windows)
[![CUDA: RTX 3050](https://img.shields.io/badge/CUDA-RTX%203050%206GB-76B900.svg)](https://developer.nvidia.com/cuda-zone)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Kural combines local, GPU-accelerated Whisper speech recognition with deep Windows voice control, designed specifically for bilingual English and Tamil users on Windows 11.

---

## Key Highlights

- **Bilingual Voice Typing & Control:** Native script Tamil (*தமிழ்*), English, and code-switched Tanglish (*"chrome open பண்ணு"*, *"notepad திற"*).
- **GPU Accelerated:** Optimized for the NVIDIA GeForce RTX 3050 (6 GB VRAM) using `large-v3-turbo` in CUDA `float16`.
- **Idle VRAM Unload:** Automatically releases GPU memory back to Windows after an inactivity period (default: 5 min), transparently reloading on next dictation.
- **Deep Windows Voice Control:**
  - Launch & switch apps indexed directly from the Windows Start Menu and Microsoft Store.
  - Multi-tier fuzzy matching and second-pass misheard verb recovery (*"oben chrome"* $\rightarrow$ *"open chrome"*).
  - Graceful window closing (`WM_CLOSE`), window snapping, minimizing, and maximizing.
  - System volume & media transport controls via Windows Core Audio.
- **Strict Guardrails:** Blocks file deletion, partition formatting, and autonomous payments. Delayed 60s cancellable window for shutdown/restart.
- **Elevated Windows UIPI Detection:** Detects when target windows run as Administrator and notifies the user instead of silently dropping synthetic input.
- **100% Local & Private:** Zero runtime telemetry, no cloud API calls, air-gapped text pipeline.

---

## Architecture Overview

```
kural/
├── engine/              # Audio capture, faster-whisper inference, VRAM lifecycle, VAD
│   ├── whisper_engine.py       # faster-whisper backend with CUDA float16 & idle unload
│   ├── audio_recorder.py       # Ring-buffer continuous capture with WASAPI resampling
│   ├── hardware_detection.py   # GPU & CUDA DLL diagnostics (cuBLAS, cuDNN)
│   ├── voice_activity_detection.py # TEN VAD speech detector
│   ├── wake_word.py            # Optional offline keyword listener
│   └── model_registry.py       # Local & HuggingFace cache management
├── control/             # Voice control brain, automation, and OS integration
│   ├── executor.py             # 5-tier command resolution hierarchy
│   ├── parser.py               # Pure intent parser (SVO/SOV, English, Tamil, Tanglish)
│   ├── app_index.py            # Start Menu & Store app indexer with fuzzy matching
│   ├── windows.py              # Window enumeration, focus, snap, and graceful WM_CLOSE
│   ├── media.py                # Windows Core Audio volume & media transport
│   ├── guardrails.py           # Safety allowlist, destructive action blocker
│   └── llm_fallback.py         # Optional air-gapped local-LLM intent fallback
├── config/              # Layered configuration & defaults
│   ├── config_manager.py       # %APPDATA%\kural\user_settings.yaml overrides & validation
│   ├── config.defaults.yaml    # Shipped engine & control defaults
│   └── commands.defaults.yaml  # Bilingual voice command triggers
├── doctor.py            # CLI diagnostic tool (kural --doctor)
├── benchmarks/          # ASR evaluation harness (WER, Tamil CER, RTF)
└── packaging/           # Standalone PyInstaller build (kural.exe)
```

---

## Getting Started

### Prerequisites

- **OS:** Windows 11 (AMD64)
- **Python:** 3.12+ (managed with `uv` or system Python)
- **GPU (Recommended):** NVIDIA RTX 3050 (or any CUDA 12 compatible GPU) with latest NVIDIA drivers

### Installation

```powershell
# Clone the repository
git clone https://github.com/mdaashir/kural.git
cd kural

# Create environment and install dependencies
uv venv
.\.venv\Scripts\activate
uv pip install -e .
```

### System Health Check

Verify your hardware, CUDA libraries, and audio setup with the built-in doctor:

```powershell
python -m kural --doctor
```

Expected diagnostic output:
```
Kural — Doctor Diagnostics
============================
Runtime:        Python 3.12+ on Windows 11 (AMD64)
GPU:            NVIDIA GeForce RTX 3050 (CUDA v6.5, cuBLAS & cuDNN available)
Config:         %APPDATA%\kural (writable)
Model:          large-v3-turbo on cuda (float16)
Idle VRAM:      5 min timeout
```

---

## Usage

### Voice Commands

Kural recognizes commands in English, formal Tamil, and colloquial Tanglish:

| Action | English | Tamil | Tanglish |
|---|---|---|---|
| **Launch App** | *"open chrome"* | *"திற குரோம்"* / *"குரோம் திற"* | *"chrome open பண்ணு"* |
| **Close App** | *"close notepad"* | *"மூடு நோட்பேடு"* / *"நோட்பேடு மூடு"* | *"notepad close பண்ணு"* |
| **Switch Window** | *"switch to edge"* | *"எட்ஜ்-க்கு போ"* | *"edge-க்கு மாற்று"* |
| **Volume Up** | *"volume up"* | *"சத்தம் ஏற்று"* | *"sound ஏத்து"* |
| **Volume Down** | *"volume down"* | *"சத்தம் குறை"* | *"sound குறை"* |
| **Mute Audio** | *"mute"* | *"ஒலியை நிறுத்து"* | *"மியூட் பண்ணு"* |
| **Media Play/Pause** | *"play"* / *"pause"* | *"பாடலை இயக்கு / நிறுத்து"* | *"play பண்ணு"* |
| **Window Snap** | *"snap left"* | *"இடதுபக்கம் மாற்று"* | *"snap left பண்ணு"* |
| **Show Desktop** | *"show desktop"* | *"டெஸ்க்டாப் காட்டு"* | *"desktop காட்டு"* |
| **Web Search** | *"search for python"* | *"பைதான் பற்றி தேடு"* | *"python தேடு"* |
| **YouTube Search** | *"search lofi on youtube"* | *"ரஜினி பாடல் யூடியூபில் தேடு"* | *"lofi youtube-ல தேடு"* |

### Benchmarks

Run the ASR benchmark harness to measure latency (RTF) and error rates (WER and Tamil CER):

```powershell
python -m benchmarks.run --models large-v3-turbo --device cuda --compute-type float16
```

### Building the Standalone Executable

To compile a self-contained Windows executable without external dependencies:

```cmd
packaging\build.bat
```
Output executable will be placed in `dist\kural\kural.exe`.

---

## Running Tests

All unit tests are designed to run 100% offline without requiring a microphone, GPU, or network download:

```powershell
# Run the complete test suite (227 tests)
pytest tests/ -q

# Run code style and format checks
ruff check .
ruff format --check .
```

---

## Attribution & Licenses

Kural is open-source under the [MIT License](LICENSE). It merges and adapts components from:
- **`drajb/whisper-local`** (fork of Pin Wang's `whisper-key-local`)
- **`ROHITCRAFTSYT/WhispLocal`** (by Rohit Burani)

Full upstream copyright lines and per-file provenance are documented in [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
