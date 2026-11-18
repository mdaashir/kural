# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/instance_manager.py
"""Single-instance process locking and graceful takeover for Kural.

Ensures only one Kural daemon runs on the system at any given time using a named
Win32 Mutex and a PID file in %APPDATA%\\kural\\kural.pid.

Rather than refusing to start when a duplicate instance is launched, Kural prefers
graceful takeover: the new instance signals the older background instance to terminate,
waits up to 5 seconds for mutex release, and takes over seamlessly.
"""

import logging
import os
import signal
import sys
import time
from pathlib import Path
from typing import Any

from kural.engine.utils import get_user_app_data_path

logger = logging.getLogger(__name__)

ERROR_ALREADY_EXISTS = 183


def get_pid_file_path(app_name: str = "kural") -> Path:
    """Return the path to the instance PID file."""
    return Path(get_user_app_data_path()) / f"{app_name.lower()}.pid"


def read_existing_pid(app_name: str = "kural") -> int | None:
    """Read PID of previously active instance if present."""
    path = get_pid_file_path(app_name)
    if not path.is_file():
        return None
    try:
        val = path.read_text(encoding="utf-8").strip()
        return int(val) if val else None
    except (ValueError, OSError):
        return None


def write_pid_file(app_name: str = "kural") -> None:
    """Record current process PID to file."""
    try:
        path = get_pid_file_path(app_name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(os.getpid()), encoding="utf-8")
    except OSError as e:
        logger.warning(f"Could not write PID file: {e}")


def cleanup_pid_file(app_name: str = "kural") -> None:
    """Remove PID file on graceful shutdown."""
    try:
        path = get_pid_file_path(app_name)
        if path.is_file():
            path.unlink()
    except OSError:
        pass


def terminate_process(pid: int) -> bool:
    """Signal an existing process to terminate."""
    if pid == os.getpid():
        return False
    try:
        os.kill(pid, signal.SIGTERM)
        return True
    except (ProcessLookupError, PermissionError, OSError) as e:
        logger.debug(f"Could not terminate PID {pid}: {e}")
        return False


def _create_win32_mutex(name: str) -> tuple[Any, bool]:
    """Create a named Win32 mutex. Returns (handle, already_exists)."""
    if sys.platform != "win32":
        # Cross-platform / test environment fallback
        return object(), False

    import ctypes

    kernel32 = ctypes.windll.kernel32
    mutex_name = f"Local\\{name}_SingleInstance"
    handle = kernel32.CreateMutexW(None, True, mutex_name)
    last_err = kernel32.GetLastError()
    already_exists = last_err == ERROR_ALREADY_EXISTS
    return handle, already_exists


def _close_win32_mutex(handle: Any) -> None:
    """Close the named Win32 mutex handle."""
    if sys.platform == "win32" and handle and handle != 0:
        try:
            import ctypes

            ctypes.windll.kernel32.CloseHandle(handle)
        except Exception:
            pass


def acquire_single_instance_lock(
    app_name: str = "kural",
    timeout: float = 5.0,
    allow_takeover: bool = True,
) -> tuple[bool, Any]:
    """Acquire single instance lock with optional graceful takeover.

    Returns:
        (success, mutex_handle)
    """
    handle, already_exists = _create_win32_mutex(app_name)

    if not already_exists:
        write_pid_file(app_name)
        logger.info(f"Single-instance lock acquired for '{app_name}'")
        return True, handle

    # A previous instance is already holding the lock
    if not allow_takeover:
        _close_win32_mutex(handle)
        logger.warning(f"Another instance of '{app_name}' is already running")
        return False, None

    old_pid = read_existing_pid(app_name)
    if old_pid:
        print(f"⚠️  Kural is already running (PID {old_pid}); replacing it...")
        terminate_process(old_pid)
    else:
        print("⚠️  Kural lock is held by another process; waiting for takeover...")

    _close_win32_mutex(handle)

    # Poll until the old instance exits and frees the lock
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(0.15)
        new_handle, still_exists = _create_win32_mutex(app_name)
        if not still_exists:
            write_pid_file(app_name)
            print("✓ Lock acquired. Continuing startup.\n")
            return True, new_handle
        _close_win32_mutex(new_handle)

    print("✗ Could not acquire single-instance lock. Another instance remains active.")
    return False, None


def release_single_instance_lock(handle: Any, app_name: str = "kural") -> None:
    """Release mutex handle and clean up PID file."""
    cleanup_pid_file(app_name)
    _close_win32_mutex(handle)
