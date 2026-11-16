# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/streaming.py
"""Live partial speech transcription and UI preview (Wispr Flow style).

Periodically snapshots the growing audio buffer while recording is active,
transcribing interim phrases and emitting live preview text to the floating pill.
Authoritative final transcription runs once on the complete audio upon stop.
"""

import logging
import threading
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


class StreamingTranscriber:
    """Periodically snapshots audio and calls on_partial with live interim words."""

    def __init__(
        self,
        audio_source: Any,
        engine: Any,
        on_partial: Callable[[str], None],
        interval: float = 0.65,
        min_seconds: float = 0.5,
        sample_rate: int = 16000,
    ):
        self._source = audio_source
        self._engine = engine
        self._on_partial = on_partial
        self._interval = interval
        self._min_samples = int(min_seconds * sample_rate)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_len = 0
        self._last_text = ""

    def start(self) -> None:
        """Start the live background snapshotting loop."""
        self._stop_event.clear()
        self._last_len = 0
        self._last_text = ""
        self._thread = threading.Thread(
            target=self._run_loop, daemon=True, name="streaming-transcriber"
        )
        self._thread.start()

    def stop(self, timeout: float = 1.0) -> None:
        """Stop the snapshotting loop."""
        self._stop_event.set()
        t = self._thread
        self._thread = None
        if t is not None and t.is_alive():
            t.join(timeout=timeout)

    def _should_emit(self, audio) -> bool:
        """Check if audio has sufficient length and has grown since the last check."""
        if audio is None or len(audio) == 0:
            return False
        # Need minimum samples and at least 0.3s of fresh audio
        return len(audio) >= self._min_samples and (len(audio) - self._last_len) >= 4800

    def _run_loop(self) -> None:
        while not self._stop_event.wait(self._interval):
            if self._stop_event.is_set():
                break
            try:
                # Capture non-destructive snapshot of current audio buffer
                snapshot = (
                    self._source.get_audio_data()
                    if hasattr(self._source, "get_audio_data")
                    else None
                )
                if not self._should_emit(snapshot):
                    continue

                self._last_len = len(snapshot)
                text = self._engine.transcribe_audio(snapshot)
                clean_text = (text or "").strip()

                if clean_text and clean_text != self._last_text:
                    self._last_text = clean_text
                    try:
                        self._on_partial(clean_text)
                    except Exception as e:
                        logger.debug(f"Error in on_partial callback: {e}")
            except Exception as e:
                logger.debug(f"Streaming preview loop error: {e}")
