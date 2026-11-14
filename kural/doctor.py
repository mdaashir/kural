# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported from drajb/whisper-local/src/whisper_key/doctor.py
# doctor.py
# `kural --doctor` diagnostic health check. Walks runtime, dependencies, config,
# GPU/CUDA libraries, audio devices, and model cache. Exit 0 = clean, 1 = issues.

import importlib
import os
import platform
import sys
from pathlib import Path

GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"

OK = f"{GREEN}[OK]{RESET}  "
WARN = f"{YELLOW}[!]{RESET}   "
FAIL = f"{RED}[X]{RESET}   "
INFO = f"{DIM}[i]{RESET}   "

CORE_PACKAGES = [
    "numpy",
    "ruamel.yaml",
]

OPTIONAL_PACKAGES = [
    "faster_whisper",
    "ctranslate2",
    "sounddevice",
    "soxr",
    "ten_vad",
]


class Check:
    def __init__(self, name: str):
        self.name = name
        self.status = None
        self.detail = ""

    def ok(self, detail: str = "") -> "Check":
        self.status = OK
        self.detail = detail
        return self

    def warn(self, detail: str = "") -> "Check":
        self.status = WARN
        self.detail = detail
        return self

    def fail(self, detail: str = "") -> "Check":
        self.status = FAIL
        self.detail = detail
        return self

    def info(self, detail: str = "") -> "Check":
        self.status = INFO
        self.detail = detail
        return self

    def print(self) -> None:
        line = f"{self.status}{self.name}"
        if self.detail:
            line += f"  {DIM}{self.detail}{RESET}"
        print(line)


def run_doctor() -> int:
    print(f"\n{BOLD}Kural — Doctor Diagnostics{RESET}\n{'=' * 28}\n")

    failures = 0
    failures += _section_runtime()
    failures += _section_gpu()
    failures += _section_dependencies()
    failures += _section_config()
    failures += _section_audio()
    failures += _section_model()

    print()
    if failures == 0:
        print(f"{GREEN}{BOLD}All checks passed.{RESET}\n")
        return 0
    print(f"{RED}{BOLD}{failures} issue(s) found.{RESET}  Review the [X] lines above.\n")
    return 1


def _section_runtime() -> int:
    print(f"{BOLD}Runtime{RESET}")
    failures = 0

    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if sys.version_info >= (3, 12):  # noqa: UP036
        Check("Python version").ok(f"{py_ver} (target 3.12+)").print()
    elif sys.version_info >= (3, 11):  # noqa: UP036
        Check("Python version").warn(f"{py_ver} (Kural prefers 3.12)").print()
    else:
        Check("Python version").fail(f"{py_ver} (need >=3.11)").print()
        failures += 1

    Check("Platform").info(
        f"{platform.system()} {platform.release()} ({platform.machine()})"
    ).print()

    try:
        from kural.engine.utils import get_version

        Check("Kural version").ok(get_version()).print()
    except Exception as e:
        Check("Kural version").fail(str(e)).print()
        failures += 1

    print()
    return failures


def _section_gpu() -> int:
    print(f"{BOLD}Hardware & GPU (Target: NVIDIA RTX 3050){RESET}")
    failures = 0

    try:
        from kural.engine.hardware_detection import (
            detect_gpu,
            find_cuda_runtime,
            missing_gpu_libraries,
        )

        vendor, name = detect_gpu()
        if name:
            Check("Detected GPU").ok(f"{name} ({vendor})").print()
        else:
            Check("Detected GPU").warn("No dedicated GPU found via nvidia-smi / WMI").print()

        cuda_ver = find_cuda_runtime()
        if cuda_ver:
            Check("CUDA runtime").ok(f"v{cuda_ver}").print()
        else:
            Check("CUDA runtime").info("Not found in standard paths (driver mode active)").print()

        missing = missing_gpu_libraries()
        if missing:
            Check("CUDA inference libraries").fail(f"Missing: {', '.join(missing)}").print()
            failures += 1
        else:
            Check("CUDA inference libraries").ok("cuBLAS & cuDNN available").print()
    except Exception as e:
        Check("GPU probe").warn(str(e)).print()

    print()
    return failures


def _section_dependencies() -> int:
    print(f"{BOLD}Dependencies{RESET}")
    failures = 0

    for pkg in CORE_PACKAGES:
        try:
            importlib.import_module(pkg)
            Check(pkg).ok("installed").print()
        except ImportError as e:
            Check(pkg).fail(f"missing ({e})").print()
            failures += 1

    for pkg in OPTIONAL_PACKAGES:
        try:
            mod = importlib.import_module(pkg)
            ver = getattr(mod, "__version__", "installed")
            Check(pkg).ok(f"v{ver}").print()
        except ImportError:
            Check(pkg).info("not installed (lazy/optional dependency)").print()

    print()
    return failures


def _section_config() -> int:
    print(f"{BOLD}Configuration{RESET}")
    failures = 0

    try:
        from kural.engine.utils import get_user_app_data_path

        cfg_dir = Path(get_user_app_data_path())
        Check("Config directory").ok(str(cfg_dir)).print()

        if not os.access(cfg_dir, os.W_OK):
            Check("Config writable").fail("Not writable").print()
            failures += 1
        else:
            Check("Config writable").ok().print()
    except Exception as e:
        Check("Config directory").fail(str(e)).print()
        return failures + 1

    try:
        from kural.config import ConfigManager

        cfg = ConfigManager(quiet=True)
        Check("ConfigManager loaded").ok().print()

        whisper_cfg = cfg.get_whisper_config()
        model_str = f"{whisper_cfg.get('model', '?')} on {whisper_cfg.get('device', '?')} ({whisper_cfg.get('compute_type', '?')})"
        Check("Selected model").info(model_str).print()

        lang = whisper_cfg.get("language", "en")
        Check("Language").info(f"{lang}").print()
    except Exception as e:
        Check("ConfigManager").fail(str(e)).print()
        failures += 1

    print()
    return failures


def _section_audio() -> int:
    print(f"{BOLD}Audio & Microphone{RESET}")
    failures = 0

    try:
        import sounddevice as sd

        default_input = sd.query_devices(kind="input")
        dev_name = default_input.get("name", "Unknown")
        sample_rate = int(default_input.get("default_samplerate", 0))
        Check("Default microphone").ok(f"{dev_name} ({sample_rate} Hz)").print()
    except Exception as e:
        Check("Audio device query").info(f"sounddevice query: {e}").print()

    try:
        from kural.engine.voice_activity_detection import HAS_TEN_VAD

        if HAS_TEN_VAD:
            Check("Voice activity detection").ok("TEN VAD ready").print()
        else:
            Check("Voice activity detection").info(
                "ten-vad not installed (silence won't auto-stop)"
            ).print()
    except Exception as e:
        Check("Voice activity detection").warn(str(e)).print()

    print()
    return failures


def _section_model() -> int:
    print(f"{BOLD}Model Cache{RESET}")
    failures = 0

    try:
        from kural.config import ConfigManager

        cfg = ConfigManager(quiet=True)
        whisper_cfg = cfg.get_whisper_config()
        model_key = whisper_cfg.get("model", "large-v3-turbo")

        idle_min = whisper_cfg.get("idle_unload_minutes", 5)
        if idle_min > 0:
            Check("Idle VRAM unload").ok(f"{idle_min} min timeout (frees GPU memory)").print()
        else:
            Check("Idle VRAM unload").info("disabled").print()

        from kural.engine.model_registry import ModelRegistry

        reg = ModelRegistry(whisper_models_config=whisper_cfg.get("models", {}))
        cached = reg.is_model_cached(model_key)
        if cached:
            Check(f"Model '{model_key}' cached").ok().print()
        else:
            Check(f"Model '{model_key}' cache").info("will download on first run (~1.5 GB)").print()
    except ImportError as e:
        Check("Model cache probe").info(f"{e} (install faster-whisper to probe cache)").print()
    except Exception as e:
        Check("Model cache probe").warn(str(e)).print()

    print()
    return failures
