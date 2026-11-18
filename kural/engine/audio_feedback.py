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
        self._play_async(
            lambda: self._play_cue_or_sound("start", self.start_sound, "SystemAsterisk", 0x00000040)
        )

    def play_stop(self) -> None:
        """Audible signal when recording stops (hotkey released, transcription started)."""
        self._play_async(
            lambda: self._play_cue_or_sound("stop", self.stop_sound, "SystemDefault", 0x00000000)
        )

    def play_complete(self) -> None:
        """Audible signal when transcription or command completes successfully."""
        self._play_async(
            lambda: self._play_cue_or_sound(
                "done", self.complete_sound, "SystemNotification", 0x00000000
            )
        )

    def play_transform(self) -> None:
        """Audible signal when a smart text rewrite or edit transform succeeds."""
        self._play_async(
            lambda: self._play_cue_or_sound(
                "transform", self.complete_sound, "SystemNotification", 0x00000000
            )
        )

    def play_error(self) -> None:
        """Audible signal when a command is blocked or transcription fails."""
        self._play_async(
            lambda: self._play_cue_or_sound("error", self.error_sound, "SystemHand", 0x00000010)
        )

    def _play_sound(
        self,
        custom_path: str = "",
        alias_name: str = "",
        fallback_icon: int = 0,
        cue_name: str = "done",
    ) -> None:
        """Backwards-compatible sound playback delegating to _play_cue_or_sound."""
        self._play_cue_or_sound(cue_name, custom_path, alias_name, fallback_icon)

    def _play_cue_or_sound(
        self, cue_name: str, custom_path: str, alias_name: str, fallback_icon: int
    ) -> None:
        if sys.platform != "win32":
            return

        import winsound

        # 1. Custom WAV file if specified by user and exists
        if custom_path and os.path.isfile(custom_path):
            winsound.PlaySound(custom_path, winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            return

        # 2. Modern synthesized soft chime (Wispr Flow style)
        if cue_name:
            try:
                from kural.engine.cues import get_cue_wav_bytes

                wav_data = get_cue_wav_bytes(cue_name)
                winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NODEFAULT)
                return
            except Exception:
                pass

        # 3. Windows system sound event by alias
        try:
            winsound.PlaySound(alias_name, winsound.SND_ALIAS | winsound.SND_NODEFAULT)
        except Exception:
            # 4. Fallback to native Windows MessageBeep
            with contextlib.suppress(Exception):
                winsound.MessageBeep(fallback_icon)
