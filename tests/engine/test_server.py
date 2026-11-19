"""Tests for kural.engine.server — OpenAI-compatible local API server."""

import io
import json
import sys
import threading
import urllib.request
import wave
from http.server import ThreadingHTTPServer
from unittest.mock import MagicMock, patch

import numpy as np

from kural.engine.server import (
    _decode_audio,
    _decode_wav_fallback,
    _parse_multipart,
    build_server_engine,
    make_handler,
)


def _generate_test_wav(
    duration_s: float = 0.1, sample_rate: int = 16000, samples: np.ndarray | None = None
) -> bytes:
    """Generate in-memory 16-bit PCM mono WAV bytes."""
    if samples is None:
        num_samples = int(duration_s * sample_rate)
        samples = (np.sin(np.linspace(0, 100, num_samples)) * 10000).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


class TestServerEngineBuild:
    def test_passes_model_registry_for_configured_alias(self):
        whisper_cfg = {
            "model": "distil-large-v3.5",
            "models": {
                "distil-large-v3.5": {
                    "source": "Systran/faster-distil-whisper-large-v3",
                    "group": "official",
                }
            },
        }
        mock_config = MagicMock()
        mock_config.get_whisper_config.return_value = whisper_cfg
        mock_registry = MagicMock()
        mock_engine = MagicMock()

        with (
            patch("kural.config.ConfigManager", return_value=mock_config),
            patch("kural.engine.model_registry.ModelRegistry", return_value=mock_registry),
            patch(
                "kural.engine.whisper_engine.WhisperEngine", return_value=mock_engine
            ) as engine_cls,
        ):
            result = build_server_engine()

        assert result is mock_engine
        assert engine_cls.call_args.kwargs["model_key"] == "distil-large-v3.5"
        assert engine_cls.call_args.kwargs["model_registry"] is mock_registry

    def test_registered_model_source_resolves_alias(self):
        registry_config = {
            "distil-large-v3.5": {
                "source": "Systran/faster-distil-whisper-large-v3",
                "group": "official",
            }
        }
        mock_config = MagicMock()
        mock_config.get_whisper_config.return_value = {
            "model": "distil-large-v3.5",
            "models": registry_config,
        }
        with (
            patch("kural.config.ConfigManager", return_value=mock_config),
            patch("kural.engine.whisper_engine.WhisperEngine") as mock_engine,
        ):
            build_server_engine()

        registry = mock_engine.call_args.kwargs["model_registry"]
        assert registry.get_source("distil-large-v3.5") == "Systran/faster-distil-whisper-large-v3"


class TestAudioDecoding:
    def test_decode_wav_fallback_resamples_when_soxr_missing(self, monkeypatch):
        samples = np.asarray([0, 1000, 2000, 3000], dtype=np.int16)
        wav_bytes = _generate_test_wav(sample_rate=8000, samples=samples)
        monkeypatch.setitem(sys.modules, "soxr", None)

        audio = _decode_wav_fallback(wav_bytes)

        assert audio.dtype == np.float32
        assert len(audio) == 8

    def test_decode_soundfile_audio_resamples_when_soxr_missing(self, monkeypatch):
        import sys
        from unittest.mock import MagicMock

        fake_soundfile = MagicMock()
        fake_soundfile.read.return_value = (np.asarray([0, 0.25, 0.5, 1.0], dtype=np.float32), 8000)
        monkeypatch.setitem(sys.modules, "soundfile", fake_soundfile)
        monkeypatch.setitem(sys.modules, "soxr", None)

        audio = _decode_audio(b"fake encoded audio")

        assert audio.dtype == np.float32
        assert len(audio) == 8
        assert audio[0] == 0.0
        assert audio[-1] == 1.0

    def test_decode_wav_fallback_16bit(self):
        wav_bytes = _generate_test_wav(0.1, 16000)
        audio = _decode_wav_fallback(wav_bytes)
        assert isinstance(audio, np.ndarray)
        assert audio.dtype == np.float32
        assert len(audio) == 1600  # 0.1s * 16000


class TestMultipartParsing:
    def test_parse_valid_multipart(self):
        boundary = "---------------------------boundary123"
        body = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="language"\r\n\r\n'
            "ta\r\n"
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="file"; filename="test.wav"\r\n'
            "Content-Type: audio/wav\r\n\r\n"
            "dummy_audio_bytes\r\n"
            f"--{boundary}--\r\n"
        ).encode()

        class DummyHandler:
            headers = {
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
            }
            rfile = io.BytesIO(body)

        fields = _parse_multipart(DummyHandler())
        assert "language" in fields
        assert fields["language"]["value"] == "ta"
        assert "file" in fields
        assert fields["file"]["data"] == b"dummy_audio_bytes"


class MockEngine:
    def __init__(self):
        self.language = "en"
        self.initial_prompt = ""

    def transcribe_audio(self, audio_array):
        return "Transcribed local audio speech"


class TestLiveServerEndpoints:
    @classmethod
    def setup_class(cls):
        cls.engine = MockEngine()
        cls.handler = make_handler(cls.engine)
        # Port 0 lets OS allocate an available port
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), cls.handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def teardown_class(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def test_get_health(self):
        url = f"http://127.0.0.1:{self.port}/health"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["status"] == "ok"
            assert data["engine"] == "kural"

    def test_get_models(self):
        url = f"http://127.0.0.1:{self.port}/v1/models"
        with urllib.request.urlopen(url) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["object"] == "list"
            assert data["data"][0]["id"] == "whisper-1"

    def test_post_transcriptions_json(self):
        url = f"http://127.0.0.1:{self.port}/v1/audio/transcriptions"
        boundary = "---------------------------boundary987"
        wav_bytes = _generate_test_wav(0.1, 16000)

        body = (
            f"--{boundary}\r\n".encode()
            + b'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
            + b"Content-Type: audio/wav\r\n\r\n"
            + wav_bytes
            + b"\r\n"
            + f"--{boundary}\r\n".encode()
            + b'Content-Disposition: form-data; name="response_format"\r\n\r\n'
            + b"json\r\n"
            + f"--{boundary}--\r\n".encode()
        )

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
            method="POST",
        )

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            res = json.loads(resp.read().decode("utf-8"))
            assert res["text"] == "Transcribed local audio speech"

    def test_post_transcriptions_plain_text(self):
        url = f"http://127.0.0.1:{self.port}/v1/audio/transcriptions"
        boundary = "---------------------------boundary555"
        wav_bytes = _generate_test_wav(0.1, 16000)

        body = (
            f"--{boundary}\r\n".encode()
            + b'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n\r\n'
            + wav_bytes
            + b"\r\n"
            + f"--{boundary}\r\n".encode()
            + b'Content-Disposition: form-data; name="response_format"\r\n\r\n'
            + b"text\r\n"
            + f"--{boundary}--\r\n".encode()
        )

        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": f"multipart/form-data; boundary={boundary}",
                "Content-Length": str(len(body)),
            },
            method="POST",
        )

        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            text = resp.read().decode("utf-8")
            assert text == "Transcribed local audio speech"
