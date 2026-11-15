"""Tests for kural.engine.server — OpenAI-compatible local API server."""

import io
import json
import threading
import urllib.request
import wave
from http.server import ThreadingHTTPServer

import numpy as np

from kural.engine.server import (
    _decode_wav_fallback,
    _parse_multipart,
    make_handler,
)


def _generate_test_wav(duration_s: float = 0.1, sample_rate: int = 16000) -> bytes:
    """Generate in-memory 16-bit PCM mono WAV bytes."""
    num_samples = int(duration_s * sample_rate)
    samples = (np.sin(np.linspace(0, 100, num_samples)) * 10000).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())
    return buf.getvalue()


class TestAudioDecoding:
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
