"""Tests for kural.engine.whisper_engine — mocks faster_whisper, no GPU/mic needed."""

import inspect
from unittest.mock import MagicMock, patch

import numpy as np
import pytest


def _make_fake_whisper_model(text=""):
    model = MagicMock()
    info = MagicMock()
    info.language = "en"
    info.language_probability = 0.99
    if text:
        seg = MagicMock()
        seg.text = text
        model.transcribe.return_value = (iter([seg]), info)
    else:
        model.transcribe.return_value = (iter([]), info)
    return model, info


@pytest.fixture()
def engine():
    from kural.engine.whisper_engine import WhisperEngine

    e = WhisperEngine.__new__(WhisperEngine)
    e.model_key = "large-v3-turbo"
    e.device = "cuda"
    e.compute_type = "float16"
    e.language = None
    e.beam_size = 5
    e.initial_prompt = None
    e.hotwords = None
    e.task = "transcribe"
    e.indic_script = "native"
    e.model, _ = _make_fake_whisper_model()
    e.logger = MagicMock()
    e.registry = None
    e.log_transcriptions = False
    e._loading_thread = None
    e._progress_callback = None
    e.vad_manager = None
    e.last_error = None
    e.allowed_languages = []
    e.last_language_outsider = None
    return e


class TestWhisperEngineDefaults:
    def test_default_model_key(self):
        from kural.engine.whisper_engine import WhisperEngine

        sig = inspect.signature(WhisperEngine.__init__)
        assert sig.parameters["model_key"].default == "large-v3-turbo"

    def test_default_device(self):
        from kural.engine.whisper_engine import WhisperEngine

        sig = inspect.signature(WhisperEngine.__init__)
        assert sig.parameters["device"].default == "cuda"

    def test_default_compute_type(self):
        from kural.engine.whisper_engine import WhisperEngine

        sig = inspect.signature(WhisperEngine.__init__)
        assert sig.parameters["compute_type"].default == "float16"


class TestTranscribeAudio:
    def test_none_model_returns_none(self, engine):
        engine.model = None
        with patch.object(engine, "_load_model", side_effect=RuntimeError("Load failed")):
            assert engine.transcribe_audio(np.zeros(16000, dtype=np.float32)) is None

    def test_empty_audio_returns_none(self, engine):
        assert engine.transcribe_audio(np.array([], dtype=np.float32)) is None

    def test_transcription_returned(self, engine):
        fake_model, _ = _make_fake_whisper_model("Hello world")
        engine.model = fake_model
        result = engine.transcribe_audio(np.zeros(16000, dtype=np.float32))
        assert result == "Hello world"

    def test_empty_transcription_returns_none(self, engine):
        fake_model, _ = _make_fake_whisper_model("")
        engine.model = fake_model
        result = engine.transcribe_audio(np.zeros(16000, dtype=np.float32))
        assert result is None

    def test_vad_manager_no_speech_skips(self, engine):
        engine.vad_manager = MagicMock()
        engine.vad_manager.is_available.return_value = True
        engine.vad_manager.check_audio_for_speech.return_value = False
        result = engine.transcribe_audio(np.zeros(16000, dtype=np.float32))
        assert result is None
        engine.model.transcribe.assert_not_called()

    def test_tamil_script_primer_injected(self, engine):
        from kural.engine.whisper_engine import SCRIPT_PRIMER_TAMIL

        fake_model, _ = _make_fake_whisper_model("வணக்கம்")
        engine.model = fake_model
        engine.language = "ta"
        engine.initial_prompt = None

        result = engine.transcribe_audio(np.zeros(16000, dtype=np.float32))
        assert result == "வணக்கம்"
        fake_model.transcribe.assert_called_once()
        kwargs = fake_model.transcribe.call_args[1]
        assert kwargs["initial_prompt"] == SCRIPT_PRIMER_TAMIL

    def test_tamil_roman_primer_injected(self, engine):
        from kural.engine.whisper_engine import ROMAN_PRIMER_TAMIL

        fake_model, _ = _make_fake_whisper_model("Vanakkam")
        engine.model = fake_model
        engine.language = "ta"
        engine.indic_script = "roman"
        engine.initial_prompt = None

        result = engine.transcribe_audio(np.zeros(16000, dtype=np.float32))
        assert result == "Vanakkam"
        fake_model.transcribe.assert_called_once()
        kwargs = fake_model.transcribe.call_args[1]
        assert kwargs["initial_prompt"] == ROMAN_PRIMER_TAMIL

    def test_custom_prompt_overrides_tamil_primer(self, engine):
        fake_model, _ = _make_fake_whisper_model("வணக்கம்")
        engine.model = fake_model
        engine.language = "ta"
        engine.initial_prompt = "Custom Tamil prompt"

        engine.transcribe_audio(np.zeros(16000, dtype=np.float32))
        kwargs = fake_model.transcribe.call_args[1]
        assert kwargs["initial_prompt"] == "Custom Tamil prompt"

    def test_exception_sets_last_error_returns_none(self, engine):
        engine.model.transcribe.side_effect = RuntimeError("CUDA OOM")
        result = engine.transcribe_audio(np.zeros(16000, dtype=np.float32))
        assert result is None
        assert engine.last_error is not None


class TestIsLoading:
    def test_not_loading_initially(self, engine):
        assert engine.is_loading() is False

    def test_get_model_source_uses_registry(self, engine):
        mock_reg = MagicMock()
        mock_reg.get_source.return_value = "Systran/faster-distil-whisper-large-v3"
        engine.registry = mock_reg
        source = engine._get_model_source("distil-large-v3.5")
        assert source == "Systran/faster-distil-whisper-large-v3"
        mock_reg.get_source.assert_called_once_with("distil-large-v3.5")
