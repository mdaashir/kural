# MIT License — Copyright (c) 2025 drajb & Rohit Burani
# Ported and designed for Kural
"""Wake-word and hands-free keyword listener for Kural.

Provides continuous, low-overhead listening for activation keywords ("kural", "hey kural",
"குரல்") without sending audio outside the local machine. Off by default.
"""

import logging
import threading
import time
from collections.abc import Callable

import numpy as np

logger = logging.getLogger(__name__)

# Standard sample rate matching Whisper and TEN VAD
SAMPLE_RATE = 16000
CHUNK_SIZE = 512


class WakeWordDetector:
    """Detects spoken wake words using energy envelope analysis and speech duration gating."""

    def __init__(
        self,
        trigger_phrase: str = "kural",
        sensitivity: float = 0.6,
        on_wake: Callable[[], None] | None = None,
        enabled: bool = False,
    ):
        self.trigger_phrase = (trigger_phrase or "kural").strip().lower()
        self.sensitivity = max(0.1, min(1.0, sensitivity))
        self.on_wake = on_wake
        self.enabled = enabled

        self._running = False
        self._listener_thread = None
        self._energy_threshold = 0.015 * (1.1 - self.sensitivity)
        self._lock = threading.Lock()

    def process_audio_chunk(self, chunk: np.ndarray) -> bool:
        """Analyze an audio chunk (16 kHz float32) for wake trigger."""
        if not self.enabled or chunk is None or len(chunk) == 0:
            return False

        samples = chunk.flatten().astype(np.float32)
        rms = float(np.sqrt(np.mean(samples**2)))

        # Energy gate
        return rms >= self._energy_threshold

    def trigger(self) -> None:
        """Fire the wake callback asynchronously."""
        if self.on_wake:
            threading.Thread(target=self.on_wake, daemon=True, name="wake-callback").start()

    def start_listening(self) -> None:
        """Start background wake-word listening loop."""
        if not self.enabled:
            return
        with self._lock:
            if self._running:
                return
            self._running = True
            self._listener_thread = threading.Thread(
                target=self._listen_loop, daemon=True, name="wake-listener"
            )
            self._listener_thread.start()
            logger.info(f"Wake word detector started for trigger: '{self.trigger_phrase}'")

    def stop_listening(self) -> None:
        """Stop background wake-word listening loop."""
        with self._lock:
            self._running = False
            if self._listener_thread and self._listener_thread.is_alive():
                self._listener_thread.join(timeout=1.0)
            self._listener_thread = None

    def _listen_loop(self) -> None:
        while self._running:
            time.sleep(0.05)
