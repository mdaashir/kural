# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported from drajb/whisper-local/src/whisper_key/platform/windows/gpu.py
# hardware_detection.py
# Identifies GPU hardware and verifies that CTranslate2 can load its CUDA/cuBLAS DLLs.
# A card being present is not the same as the runtime working. Reports missing DLLs
# before inference starts to prevent hangs.

import ctypes
import glob
import logging
import os
import pathlib
import site
import subprocess
import sys

logger = logging.getLogger(__name__)

_NO_WINDOW = {"creationflags": 0x08000000} if sys.platform == "win32" else {}

# The CUDA libraries that CTranslate2's CUDA build (CUDA 12 + cuDNN 9 or 8)
# loads by bare name on the FIRST INFERENCE.
# Each entry is a tuple of acceptable filenames; at least one must load.
_CUDA_RUNTIME_LIBRARIES = (
    ("cublas64_12.dll",),
    ("cublasLt64_12.dll",),
    ("cudnn64_9.dll", "cudnn64_8.dll"),
    ("cudnn_ops64_9.dll", "cudnn_ops_infer64_8.dll"),
    ("cudnn_cnn64_9.dll", "cudnn_cnn_infer64_8.dll"),
)


def _status(msg: str) -> None:
    print(msg)
    logger.debug(msg.strip())


def detect_gpu() -> tuple[str | None, str | None]:
    """Detect GPU vendor and model name. Returns (vendor, name) or (None, None)."""
    nvidia = _detect_nvidia_gpu()
    if nvidia:
        return "nvidia", nvidia

    amd = _detect_amd_gpu()
    if amd:
        return "amd", amd

    return None, None


def _detect_nvidia_gpu() -> str | None:
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=5,
            **_NO_WINDOW,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def _detect_amd_gpu() -> str | None:
    if sys.platform != "win32":
        return None
    try:
        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_VideoController | Where-Object {$_.Name -match 'AMD|Radeon'}).Name",
            ],
            capture_output=True,
            text=True,
            timeout=5,
            **_NO_WINDOW,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split("\n")[0].strip()
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass
    return None


def find_cuda_runtime() -> str | None:
    """Find installed CUDA runtime version string (e.g. '12.4'), or None."""
    if sys.platform != "win32":
        return None

    search_dirs = []

    cuda_path = os.environ.get("CUDA_PATH")
    if cuda_path:
        search_dirs.append(os.path.join(cuda_path, "bin"))

    try:
        for sp in site.getsitepackages():
            search_dirs.append(os.path.join(sp, "nvidia", "cuda_runtime", "bin"))
    except Exception:
        pass

    search_dirs.extend(os.environ.get("PATH", "").split(os.pathsep))

    for search_dir in search_dirs:
        if not search_dir or not os.path.isdir(search_dir):
            continue
        for dll_path in glob.glob(os.path.join(search_dir, "cudart64_*.dll")):
            version = _get_cuda_version_from_dll(dll_path)
            if version:
                return version

    return None


def _get_cuda_version_from_dll(dll_path: str) -> str | None:
    try:
        cudart = ctypes.CDLL(dll_path)
        cudart.cudaRuntimeGetVersion.restype = ctypes.c_int
        cudart.cudaRuntimeGetVersion.argtypes = [ctypes.POINTER(ctypes.c_int)]
        version = ctypes.c_int(0)
        if cudart.cudaRuntimeGetVersion(ctypes.byref(version)) == 0:
            v = version.value
            major = v // 1000
            minor = (v % 1000) // 10
            return f"{major}.{minor}"
    except (OSError, AttributeError):
        pass
    return None


def _library_loads(name: str) -> bool:
    if sys.platform != "win32":
        return True
    try:
        # winmode=0 searches standard Windows paths including PATH
        ctypes.WinDLL(name, winmode=0)
        return True
    except OSError:
        return False


def missing_gpu_libraries() -> list[str]:
    """CUDA libraries that CTranslate2 needs but cannot load. Empty when setup is complete."""
    if sys.platform != "win32":
        return []

    # If ctranslate2 is not installed or not built for CUDA, don't flag missing CUDA libs
    if _detect_ct2_variant() != "cuda":
        return []

    return [
        names[0]
        for names in _CUDA_RUNTIME_LIBRARIES
        if not any(_library_loads(name) for name in names)
    ]


def _detect_ct2_variant() -> str:
    try:
        import ctranslate2
    except ImportError:
        return "not_installed"

    file_path = getattr(ctranslate2, "__file__", None)
    if not file_path:
        return "cuda"

    dll_path = pathlib.Path(file_path).parent / "ctranslate2.dll"
    if not dll_path.exists():
        return "cuda"

    # Quick check for ROCm imports
    try:
        with open(dll_path, "rb") as f:
            content = f.read(1024 * 1024)
            if b"amdhip" in content or b"hipblas" in content:
                return "rocm"
    except Exception:
        pass

    return "cuda"


def test_ct2_gpu(ct2_variant: str = "cuda") -> bool:
    """Verify whether CTranslate2 can actually run on GPU."""
    try:
        import ctranslate2

        if not ctranslate2.get_supported_compute_types("cuda"):
            return False
    except Exception:
        return False

    if ct2_variant == "cuda":
        missing = missing_gpu_libraries()
        if missing:
            _status(f"   ✗ Missing CUDA libraries: {', '.join(missing)}")
            return False
    return True


def detect_and_print(configured_device: str = "cuda") -> tuple[str | None, str | None, bool]:
    """Inspect system hardware and print human-friendly status lines.

    Returns (vendor, gpu_name, ct2_gpu_available).
    """
    vendor, name = detect_gpu()
    if not name:
        return None, None, False

    _status("🖥️ System check...")
    _status(f"   ✓ Detected {name}")

    if vendor == "nvidia":
        runtime_ver = find_cuda_runtime()
        if runtime_ver:
            _status(f"   ✓ NVIDIA CUDA {runtime_ver} runtime available")
        else:
            _status("   ! NVIDIA CUDA runtime not found (driver mode)")

    ct2_var = _detect_ct2_variant()
    if ct2_var == "not_installed":
        _status("   ! CTranslate2 not installed")
        return vendor, name, False

    ct2_works = test_ct2_gpu(ct2_var)
    if ct2_works:
        _status("   ✓ GPU acceleration available")
    else:
        _status("   ! GPU acceleration unavailable — will fall back to CPU")

    return vendor, name, ct2_works
