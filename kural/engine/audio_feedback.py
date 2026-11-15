# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/audio_feedback.py
"""Audible feedback cues for voice typing and voice control.

Plays short, non-blocking confirmation sounds when recording starts, stops, completes,
or errors. On Windows, uses Python's standard library `winsound` with native Windows system
sound events or custom .wav files. Playback is strictly fire-and-forget on a daemon thread
so it never blocks audio capture or dictation typing.
"""

import contextlib
import logging
import os
import sys
import threading
from collections.abc import Callable

logger = logging.getLogger(__name__)


class AudioFeedback:
    """Manages asynchronous audible feedback cues for hotkey and transcription events."""

    def __init__(
        self,
        enabled: bool = True,
        start_sound: str = "",
        stop_sound: str = "",
        complete_sound: str = "",
        error_sound: str = "",
    ):
        self.enabled = enabled
        self.start_sound = self._resolve_path(start_sound)
        self.stop_sound = self._resolve_path(stop_sound)
        self.complete_sound = self._resolve_path(complete_sound)
        self.error_sound = self._resolve_path(error_sound)

    def _resolve_path(self, path: str) -> str:
        if not path:
            return ""
        clean = os.path.expanduser(os.path.expandvars(path.strip()))
        return clean if os.path.isfile(clean) else ""

    def _play_async(self, action: Callable[[], None]) -> None:
        if not self.enabled:
            return

        def _worker():
            try:
                action()
            except Exception as e:
                logger.debug(f"Audio feedback playback failed: {e}")

        threading.Thread(target=_worker, daemon=True, name="audio-feedback").start()

    def play_start(self) -> None:
        """Audible signal when recording starts (hotkey pressed)."""
        self._play_async(lambda: self._play_sound(self.start_sound, "SystemAsterisk", 0x00000040))

    def play_stop(self) -> None:
        """Audible signal when recording stops (hotkey released, transcription started)."""
        self._play_async(lambda: self._play_sound(self.stop_sound, "SystemDefault", 0x00000000))

    def play_complete(self) -> None:
        """Audible signal when transcription or command completes successfully."""
        self._play_async(
            lambda: self._play_sound(self.complete_sound, "SystemNotification", 0x00000000)
        )

    def play_error(self) -> None:
        """Audible signal when a command is blocked or transcription fails."""
        self._play_async(lambda: self._play_sound(self.error_sound, "SystemHand", 0x00000010))

    def _play_sound(self, custom_path: str, alias_name: str, fallback_icon: int) -> None:
        if sys.platform != "win32":
            return

        import winsound

        # 1. Custom WAV file if specified and exists
        if custom_path and os.path.isfile(custom_path):
            winsound.PlaySound(custom_path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            return

        # 2. Windows system sound event by alias
        try:
            winsound.PlaySound(alias_name, winsound.SND_ALIAS | winsound.SND_NODEFAULT)
        except Exception:
            # 3. Fallback to native Windows MessageBeep
            with contextlib.suppress(Exception):
                winsound.MessageBeep(fallback_icon)
