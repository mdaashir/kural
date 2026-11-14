# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/GUARDRAILS.md and whisp/commands.py
"""Safety guardrails for voice control actions.

Enforces an allowlist of permitted voice actions, prevents autonomous payments,
blocks file deletions, ensures application termination is always graceful, and
provides a 60-second cancellable window for system power commands (shutdown/restart).
"""

import logging
import re
import subprocess
import threading

logger = logging.getLogger(__name__)

CREATE_NO_WINDOW = 0x08000000

# Phrases indicating destructive file operations that must NEVER be executed by voice
FORBIDDEN_FILE_PATTERNS = [
    re.compile(
        r"\b(?:delete|erase|remove|destroy|trash|wipe|format)\b.*\b(?:file|folder|directory|drive|disk|partition)\b",
        re.I,
    ),
    re.compile(r"\b(?:rm|del|rmdir|erase|format)\s+[/\\a-zA-Z0-9_\-\.]+", re.I),
    re.compile(r"\bformat\s+[a-zA-Z]:", re.I),
]

# Phrases indicating financial or transactional actions that must NEVER proceed autonomously
TRANSACTION_PATTERNS = [
    re.compile(
        r"\b(?:pay|purchase|buy|checkout|order)\b.*\b(?:now|money|dollar|rupee|card|bank|cart)\b",
        re.I,
    ),
    re.compile(r"\b(?:send|transfer)\b.*\b(?:money|funds|payment|crypto)\b", re.I),
]

# Process names and window titles that must NEVER be closed or terminated
PROTECTED_PROCESSES = frozenset(
    [
        "explorer",
        "shell",
        "taskbar",
        "dwm",
        "lsass",
        "csrss",
        "services",
        "smss",
        "kural",
        "kural.exe",
    ]
)


class GuardrailsViolation(Exception):
    """Raised when a voice action violates safety policies."""


class Guardrails:
    """Evaluates and enforces safety boundaries on proposed actions."""

    def __init__(self, shutdown_delay_sec: int = 60):
        self.shutdown_delay_sec = shutdown_delay_sec
        self._pending_shutdown_timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def check_command_safety(self, phrase: str) -> tuple[bool, str]:
        """Verify whether a spoken command phrase is safe to process.

        Returns (is_safe, reason_if_blocked).
        """
        phrase = phrase.strip().lower()

        # 1. Check for forbidden file destruction
        for pattern in FORBIDDEN_FILE_PATTERNS:
            if pattern.search(phrase):
                msg = "Blocked: File deletion and formatting are not permitted by voice."
                logger.warning(f"Guardrail triggered for '{phrase}': {msg}")
                return False, msg

        # 2. Check for autonomous financial transactions
        for pattern in TRANSACTION_PATTERNS:
            if pattern.search(phrase):
                msg = "Blocked: Purchases and payments cannot be completed autonomously by voice."
                logger.warning(f"Guardrail triggered for '{phrase}': {msg}")
                return False, msg

        return True, ""

    def is_protected_target(self, target_name: str) -> bool:
        """Check if an app or window name is critical system infrastructure."""
        clean = (target_name or "").strip().lower()
        # Strip path or extension if present
        clean = clean.split("\\")[-1].split("/")[-1]
        if clean.endswith(".exe"):
            clean = clean[:-4]
        return clean in PROTECTED_PROCESSES

    def schedule_shutdown(self, restart: bool = False) -> tuple[bool, str]:
        """Schedule a delayed system shutdown or restart with a cancellation window."""
        with self._lock:
            # Cancel any existing pending timer
            if self._pending_shutdown_timer:
                self._pending_shutdown_timer.cancel()
                self._pending_shutdown_timer = None

            flag = "/r" if restart else "/s"
            cmd = f"shutdown {flag} /t {self.shutdown_delay_sec} /c \"Kural scheduled power action. Say 'cancel shutdown' to abort.\""

            try:
                subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    timeout=5,
                    creationflags=CREATE_NO_WINDOW,
                )
            except Exception as e:
                return False, f"Could not schedule system power command: {e}"

            action_name = "Restart" if restart else "Shutdown"
            return (
                True,
                f"{action_name} scheduled in {self.shutdown_delay_sec} seconds. Say 'cancel shutdown' to abort.",
            )

    def cancel_shutdown(self) -> tuple[bool, str]:
        """Cancel a pending scheduled shutdown or restart."""
        with self._lock:
            try:
                out = subprocess.run(
                    "shutdown /a",
                    shell=True,
                    capture_output=True,
                    timeout=5,
                    creationflags=CREATE_NO_WINDOW,
                )
                if out.returncode == 0:
                    return True, "Scheduled power action was cancelled."
                return False, "No scheduled shutdown was active to cancel."
            except Exception as e:
                return False, f"Could not cancel shutdown: {e}"


# Singleton instance for system-wide guardrail enforcement
default_guardrails = Guardrails()
