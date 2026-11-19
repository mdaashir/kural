# MIT License — Copyright (c) 2026 Kural Project
# Inspired by anomalyco/hex (src/audio/output_ducking.rs)
"""Automatic output audio ducking during speech recording.

A single worker owns both lowering and restoration so stopping a short recording
cannot leave playback lowered after the capture ends.
"""

import logging
import threading

logger = logging.getLogger(__name__)


class AudioDucker:
    """Lower system playback volume while recording and restore it on stop."""

    def __init__(self, enabled: bool = False, factor: float = 0.25):
        self.enabled = bool(enabled)
        self.factor = max(0.0, min(1.0, float(factor)))
        self._is_ducked = False
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread: threading.Thread | None = None

    def start(self, factor: float | None = None) -> None:
        """Lower playback volume on a background thread, if not already active."""
        if not self.enabled:
            return
        duck_factor = self.factor if factor is None else max(0.0, min(1.0, float(factor)))
        with self._lock:
            # Do not overlap a new ramp with a worker still restoring volume.
            if self._is_ducked or (self._worker_thread and self._worker_thread.is_alive()):
                return
            self._is_ducked = True
            self._stop_event = threading.Event()
            stop_event = self._stop_event
            self._worker_thread = threading.Thread(
                target=self._run,
                args=(duck_factor, stop_event),
                daemon=True,
                name="audio-ducking",
            )
            self._worker_thread.start()

    def restore(self) -> None:
        """Request restoration; the ducking worker completes it asynchronously."""
        if not self.enabled:
            return
        with self._lock:
            if self._is_ducked:
                self._is_ducked = False
                self._stop_event.set()

    def _run(self, factor: float, stop_event: threading.Event) -> None:
        from kural.control.media import get_volume, set_volume

        original: int | None = None
        target: int | None = None
        lowered = False
        try:
            original = get_volume()
            if original is None or original <= 0 or stop_event.is_set():
                return
            target = max(0, min(100, int(round(original * factor))))
            for step in range(1, 5):
                if stop_event.is_set():
                    break
                set_volume(int(original + (target - original) * step / 4))
                if stop_event.wait(0.025):
                    break
            else:
                lowered = True
            if lowered:
                stop_event.wait()

            current = get_volume()
            if current is None:
                logger.warning("Cannot read playback volume to restore it; using last ramp target.")
                current = target if lowered else original
            # Once the ramp has settled, a manual change belongs to the user.
            if lowered and abs(current - target) > 5:
                logger.debug("User manually adjusted volume during dictation; skipping restore")
                return
            for step in range(1, 6):
                set_volume(int(current + (original - current) * step / 5))
                if step < 5:
                    stop_event.wait(0.04)
        except Exception:
            logger.exception("Audio ducking or restoration failed")
        finally:
            with self._lock:
                # An unavailable endpoint or a failed read also ends this capture.
                self._is_ducked = False
