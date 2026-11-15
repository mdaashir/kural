# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/autostart.py
"""Manages Windows startup registry keys (HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run).

Allows Kural to launch automatically at Windows login. Windowless launching via
`pythonw.exe` ensures no console terminal flashes on user login.
Opt-in only — never activated without explicit user consent.
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

WIN_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
WIN_VALUE_NAME = "Kural"


def _get_windowless_python(exe_path: str) -> str:
    """Return pythonw.exe if available in the same directory, otherwise return exe_path."""
    p = Path(exe_path)
    if p.name.lower() == "python.exe":
        w = p.with_name("pythonw.exe")
        if w.exists():
            return str(w)
    return exe_path


def build_launch_command(windowless: bool = True) -> list[str]:
    """Build the command line arguments required to relaunch Kural."""
    exe = sys.executable

    # Frozen executable (PyInstaller bundle)
    if getattr(sys, "frozen", False) or exe.lower().endswith("kural.exe"):
        return [exe]

    runner = _get_windowless_python(exe) if (windowless and sys.platform == "win32") else exe
    return [runner, "-m", "kural"]


def build_command_string(parts: list[str] | None = None) -> str:
    """Format launch parts into a properly quoted Windows registry command string."""
    command_parts = parts if parts is not None else build_launch_command(windowless=True)
    return " ".join(f'"{p}"' if " " in p else p for p in command_parts)


def is_autostart_enabled() -> bool:
    """Check if Kural is registered to start automatically at login."""
    if sys.platform != "win32":
        return False
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIN_RUN_KEY) as key:
            winreg.QueryValueEx(key, WIN_VALUE_NAME)
        return True
    except (FileNotFoundError, OSError, ImportError):
        return False


def get_stored_autostart_command() -> str:
    """Retrieve the currently stored autostart command string, or empty string if not set."""
    if sys.platform != "win32":
        return ""
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIN_RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, WIN_VALUE_NAME)
        return str(value or "")
    except (FileNotFoundError, OSError, ImportError):
        return ""


def enable_autostart() -> bool:
    """Register Kural in HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run."""
    if sys.platform != "win32":
        logger.warning("Autostart via Windows registry is only supported on Windows.")
        return False
    try:
        import winreg

        cmd = build_command_string()
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, WIN_RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, WIN_VALUE_NAME, 0, winreg.REG_SZ, cmd)
        logger.info(f"Autostart enabled in registry Run key: {cmd}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable autostart: {e}")
        return False


def disable_autostart() -> bool:
    """Remove Kural from HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run."""
    if sys.platform != "win32":
        return True
    try:
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, WIN_RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, WIN_VALUE_NAME)
        except FileNotFoundError:
            pass
        logger.info("Autostart disabled (Run key removed)")
        return True
    except Exception as e:
        logger.error(f"Failed to disable autostart: {e}")
        return False
