"""Tests for kural.engine.streaming — live partial speech transcription and UI preview."""

import time

import numpy as np

from kural.engine.streaming import StreamingTranscriber


class DummySource:
    def __init__(self):
        self.audio = np.zeros(16000, dtype=np.float32)

    def get_audio_data(self):
        return self.audio


class DummyEngine:
    def __init__(self):
        self.calls = 0

    def transcribe_audio(self, audio):
        self.calls += 1
        return f"Partial text {self.calls}"


class TestStreamingTranscriber:
    def test_should_emit_conditions(self):
        transcriber = StreamingTranscriber(
            audio_source=None,
            engine=None,
            on_partial=lambda _: None,
            min_seconds=0.5,
            sample_rate=16000,
        )

        assert transcriber._should_emit(None) is False
        assert transcriber._should_emit(np.zeros(2000)) is False  # Too short (<0.5s)
        assert transcriber._should_emit(np.zeros(16000)) is True  # 1s >= 0.5s

        # Subsequent check with no growth
        transcriber._last_len = 16000
        assert transcriber._should_emit(np.zeros(16000)) is False
        # Grows by 5000 samples (>=4800 threshold)
        assert transcriber._should_emit(np.zeros(21000)) is True

    def test_streaming_loop_emits_partial(self):
        source = DummySource()
        engine = DummyEngine()
        partials = []

        transcriber = StreamingTranscriber(
            audio_source=source,
            engine=engine,
            on_partial=lambda t: partials.append(t),
            interval=0.05,
            min_seconds=0.1,
        )

        transcriber.start()
        time.sleep(0.15)
        # Feed fresh audio
        source.audio = np.zeros(24000, dtype=np.float32)
        time.sleep(0.15)
        transcriber.stop()

        assert len(partials) >= 1
        assert "Partial text" in partials[0]

    def test_stop_gracefully_joins(self):
        transcriber = StreamingTranscriber(
            audio_source=DummySource(),
            engine=DummyEngine(),
            on_partial=lambda _: None,
            interval=0.1,
        )
        transcriber.start()
        assert transcriber._thread is not None
        assert transcriber._thread.is_alive()

        transcriber.stop()
        assert transcriber._thread is None

    def test_late_partial_discarded_after_stop(self):
        import threading

        in_transcribe = threading.Event()
        release_transcribe = threading.Event()
        partials = []

        class SlowEngine:
            def transcribe_audio(self, _audio):
                in_transcribe.set()
                release_transcribe.wait(timeout=2.0)
                return "Late partial that should be discarded"

        transcriber = StreamingTranscriber(
            audio_source=DummySource(),
            engine=SlowEngine(),
            on_partial=lambda t: partials.append(t),
            interval=0.01,
            min_seconds=0.1,
        )

        transcriber.start()
        # Wait until worker enters transcribe_audio
        assert in_transcribe.wait(timeout=2.0)
        # Stop transcriber while inference is in flight
        transcriber.stop(timeout=0.01)
        # Release the slow inference
        release_transcribe.set()
        time.sleep(0.1)

        # The late partial must be discarded because stop was called
        assert partials == []
