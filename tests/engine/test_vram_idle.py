"""Tests for idle VRAM unload in kural.engine.whisper_engine — fully mocked, 0 GPU needed."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


@pytest.fixture()
def mock_engine():
    from kural.engine.whisper_engine import WhisperEngine

    engine = WhisperEngine.__new__(WhisperEngine)
    engine.model_key = "large-v3-turbo"
    engine.device = "cuda"
    engine.compute_type = "float16"
    engine.idle_unload_minutes = 5
    engine._idle_timer = None
    engine.language = "en"
    engine.beam_size = 5
    engine.initial_prompt = None
    engine.hotwords = None
    engine.task = "transcribe"
    engine.vad_manager = None
    engine.allowed_languages = []
    engine.last_error = None
    engine.last_language_outsider = None
    engine.log_transcriptions = False
    engine.logger = MagicMock()
    import threading

    engine._idle_lock = threading.Lock()
    engine.model = MagicMock()
    return engine


class TestIdleVRAMUnload:
    def test_unload_model_clears_model_reference(self, mock_engine):
        assert mock_engine.is_model_loaded() is True
        mock_engine._unload_model()
        assert mock_engine.model is None
        assert mock_engine.is_model_loaded() is False

    def test_start_idle_timer_sets_timer(self, mock_engine):
        mock_engine.idle_unload_minutes = 5
        mock_engine._start_idle_timer()
        assert mock_engine._idle_timer is not None
        mock_engine._cancel_idle_timer()
        assert mock_engine._idle_timer is None

    def test_disabled_idle_timer_when_zero(self, mock_engine):
        mock_engine.idle_unload_minutes = 0
        mock_engine._start_idle_timer()
        assert mock_engine._idle_timer is None

    def test_transcribe_reloads_if_unloaded(self, mock_engine):
        # Model starts unloaded
        mock_engine.model = None
        fake_model = MagicMock()
        seg = MagicMock()
        seg.text = "Testing reload"
        info = MagicMock()
        info.language = "en"
        info.language_probability = 0.99
        fake_model.transcribe.side_effect = lambda *a, **k: ([seg], info)

        with patch.object(
            mock_engine,
            "_load_model",
            side_effect=lambda: setattr(mock_engine, "model", fake_model),
        ):
            res = mock_engine.transcribe_audio(np.zeros(16000, dtype=np.float32))
            assert res == "Testing reload"
            assert mock_engine.model is not None

        mock_engine._cancel_idle_timer()
