# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/terminal_title.py
"""Shows app state in the terminal's tab/window title ("<prefix> Kural") via ANSI OSC 0.

Provides an immediate secondary status surface for users running Kural in a visible
terminal (PowerShell, Windows Terminal, CMD, or VS Code): the tab header shows
status even when the floating pill or tray icon is hidden.

Transitions:
- idle: "Kural"
- recording: pulsing "🔴 Kural" <-> "⚪ Kural"
- processing: "⏳ Kural"

Writes are skipped entirely when stdout is not a TTY (pythonw, redirected logs, windowless exe),
preventing escape codes from polluting log files.
"""

import logging
import sys
import threading

logger = logging.getLogger(__name__)

_APP_TITLE = "Kural"
_STATIC_SECONDS = 60.0

_DEFAULTS: dict[str, list | str] = {
    "idle": "",
    "recording": [["🔴", 1.2], ["⚪", 0.8]],
    "processing": "⏳",
}


def _compose_title(prefix: str) -> str:
    """Format window/tab title string."""
    clean = str(prefix).strip()
    return f"{clean} {_APP_TITLE}" if clean else _APP_TITLE


class TerminalTitle:
    """Manages dynamic ANSI OSC 0 terminal tab title animations."""

    def __init__(self, frames_config: dict | None = None):
        try:
            self._enabled = bool(
                sys.stdout is not None and hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
            )
        except (ValueError, OSError):
            self._enabled = False

        self._frames = self._parse_frames(frames_config)
        self._state = "idle"
        self._frame_index = 0
        self._lock = threading.Lock()
        self._tick = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

        if self._enabled:
            idle_frames = self._frames.get("idle", [(_APP_TITLE, _STATIC_SECONDS)])
            self._emit(idle_frames[0][0])

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def _parse_frames(self, frames_config: dict | None) -> dict[str, list[tuple[str, float]]]:
        if not isinstance(frames_config, dict):
            frames_config = {}
        frames: dict[str, list[tuple[str, float]]] = {}
        for state, default_val in _DEFAULTS.items():
            val = frames_config.get(state, default_val)
            frames[state] = self._parse_state(state, val, default_val)
        return frames

    def _parse_state(
        self, state: str, value: object, default_value: object
    ) -> list[tuple[str, float]]:
        if value is None or isinstance(value, (str, int, float)):
            return [(_compose_title(str(value) if value is not None else ""), _STATIC_SECONDS)]

        parsed: list[tuple[str, float]] = []
        if isinstance(value, list):
            for entry in value:
                try:
                    prefix, seconds = entry
                    dur = float(seconds)
                    if dur > 0:
                        parsed.append((_compose_title(str(prefix)), dur))
                except (TypeError, ValueError):
                    pass

        if parsed:
            return parsed
        return self._parse_state(state, default_value, default_value)

    def start(self) -> None:
        """Launch the background title animation loop."""
        if not self._enabled or (self._thread and self._thread.is_alive()):
            return
        self._stop.clear()
        self._tick.clear()
        self._thread = threading.Thread(
            target=self._animation_loop, daemon=True, name="terminal-title"
        )
        self._thread.start()

    def update_state(self, new_state: str) -> None:
        """Update terminal title state immediately on runtime state changes."""
        if not self._enabled:
            return
        clean_state = new_state.lower().strip()
        with self._lock:
            if clean_state == self._state:
                return
            self._state = clean_state
            self._frame_index = 0
        self._tick.set()

    def stop(self) -> None:
        """Stop animation thread and reset terminal title."""
        if not self._enabled:
            return
        self._stop.set()
        self._tick.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._thread = None
        self._emit(_APP_TITLE)

    def _animation_loop(self) -> None:
        while not self._stop.is_set():
            with self._lock:
                frames = self._frames.get(
                    self._state, self._frames.get("idle", [(_APP_TITLE, _STATIC_SECONDS)])
                )
                title, interval = frames[self._frame_index % len(frames)]
                self._frame_index += 1

            self._emit(title)
            self._tick.wait(timeout=interval)
            self._tick.clear()

    def _emit(self, title: str) -> None:
        if not self._enabled:
            return
        try:
            sys.stdout.write(f"\033]0;{title}\007")
            sys.stdout.flush()
        except (ValueError, OSError):
            self._enabled = False
            self._stop.set()
