# MIT License — Copyright (c) 2026 Kural Project
# Inspired by anomalyco/hex (src/audio/output_ducking.rs)
"""Automatic output audio ducking during speech recording.

Gracefully lowers the system playback volume (e.g. music, videos, podcasts)
while dictating so speaker audio does not bleed into the microphone, and
smoothly restores volume when recording finishes or cancels.
"""

import logging
import threading
import time

logger = logging.getLogger(__name__)


class AudioDucker:
    """Manages automatic system audio volume ducking and smooth restoration."""

    def __init__(self, enabled: bool = False, factor: float = 0.25):
        self.enabled = bool(enabled)
        self.factor = max(0.0, min(1.0, float(factor)))
        self._original_volume: int | None = None
        self._target_volume: int | None = None
        self._is_ducked = False
        self._lock = threading.Lock()
        self._worker_thread: threading.Thread | None = None

    def start(self, factor: float | None = None) -> None:
        """Lower system playback volume asynchronously on a daemon thread."""
        if not self.enabled:
            return

        with self._lock:
            if self._is_ducked:
                return
            self._is_ducked = True

        duck_factor = self.factor if factor is None else max(0.0, min(1.0, float(factor)))

        def _duck_worker():
            try:
                from kural.control.media import get_volume, set_volume

                current = get_volume()
                if current is None or current <= 0:
                    return

                with self._lock:
                    self._original_volume = current
                    # Reduce volume proportionally to factor
                    target = max(0, min(100, int(round(current * duck_factor))))
                    self._target_volume = target

                # Smoothly ramp down over ~100ms in 4 steps to avoid abrupt pop/click
                steps = 4
                step_sleep = 0.025
                for i in range(1, steps + 1):
                    vol = int(current + (target - current) * (i / steps))
                    set_volume(vol)
                    time.sleep(step_sleep)

            except Exception as e:
                logger.debug(f"Audio ducking failed: {e}")

        self._worker_thread = threading.Thread(
            target=_duck_worker, daemon=True, name="audio-ducking-lower"
        )
        self._worker_thread.start()

    def restore(self) -> None:
        """Smoothly restore system volume to pre-ducked level asynchronously."""
        if not self.enabled:
            return

        with self._lock:
            if not self._is_ducked:
                return
            self._is_ducked = False
            original = self._original_volume
            target = self._target_volume
            self._original_volume = None
            self._target_volume = None

        if original is None:
            return

        def _restore_worker():
            try:
                from kural.control.media import get_volume, set_volume

                current = get_volume()
                # If user manually changed volume during dictation, respect user choice
                if current is not None and target is not None and abs(current - target) > 5:
                    logger.debug("User manually adjusted volume during dictation; skipping restore")
                    return

                start_vol = current if current is not None else (target or 0)

                # Smoothly ramp back up over ~200ms in 5 steps so audio doesn't jump
                steps = 5
                step_sleep = 0.04
                for i in range(1, steps + 1):
                    vol = int(start_vol + (original - start_vol) * (i / steps))
                    set_volume(vol)
                    time.sleep(step_sleep)

            except Exception as e:
                logger.debug(f"Audio restoration failed: {e}")

        threading.Thread(target=_restore_worker, daemon=True, name="audio-ducking-restore").start()
