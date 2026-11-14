"""Tests for kural.engine.wake_word — testing keyword and audio chunk processing."""

import time
from unittest.mock import MagicMock

import numpy as np

from kural.engine.wake_word import WakeWordDetector


class TestWakeWordDetector:
    def test_disabled_by_default(self):
        detector = WakeWordDetector(enabled=False)
        chunk = np.ones(512, dtype=np.float32)
        assert detector.process_audio_chunk(chunk) is False

    def test_silence_chunk_does_not_trigger(self):
        detector = WakeWordDetector(enabled=True)
        silent = np.zeros(512, dtype=np.float32)
        assert detector.process_audio_chunk(silent) is False

    def test_audible_chunk_triggers(self):
        detector = WakeWordDetector(enabled=True, sensitivity=0.8)
        # 0.5 amplitude sine wave has plenty of energy
        t = np.linspace(0, 0.032, 512, endpoint=False)
        tone = (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
        assert detector.process_audio_chunk(tone) is True

    def test_empty_or_none_chunk_safe(self):
        detector = WakeWordDetector(enabled=True)
        assert detector.process_audio_chunk(None) is False
        assert detector.process_audio_chunk(np.array([], dtype=np.float32)) is False

    def test_trigger_fires_callback_asynchronously(self):
        callback = MagicMock()
        detector = WakeWordDetector(enabled=True, on_wake=callback)
        detector.trigger()
        time.sleep(0.05)
        callback.assert_called_once()

    def test_start_stop_listening_lifecycle(self):
        detector = WakeWordDetector(enabled=True)
        detector.start_listening()
        assert detector._running is True
        detector.stop_listening()
        assert detector._running is False
