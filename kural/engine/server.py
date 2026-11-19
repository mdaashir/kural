# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/local_server.py
"""Local OpenAI-compatible Whisper API server.

Serves the standard OpenAI Audio transcriptions endpoint:
  POST /v1/audio/transcriptions  — multipart audio upload, returns {"text": "..."}
  GET  /v1/models                — OpenAI-compatible model listing
  GET  /health                   — liveness check

Runs on 127.0.0.1 loopback for strict local privacy. Zero extra framework dependencies
(uses standard library http.server).
"""

import io
import json
import logging
import threading
import wave
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 7777
MAX_UPLOAD_BYTES = 500 * 1024 * 1024  # 500 MB hard cap


def build_server_engine():
    """Build and warm up the Whisper engine from user configuration."""
    from kural.config import ConfigManager
    from kural.engine.model_registry import ModelRegistry
    from kural.engine.whisper_engine import WhisperEngine

    cm = ConfigManager(quiet=True)
    w_cfg = cm.get_whisper_config()
    model_registry = ModelRegistry(whisper_models_config=w_cfg.get("models", {}))
    return WhisperEngine(
        model_key=w_cfg.get("model", "large-v3-turbo"),
        device=w_cfg.get("device", "cuda"),
        compute_type=w_cfg.get("compute_type", "float16"),
        language=w_cfg.get("language", "en"),
        beam_size=int(w_cfg.get("beam_size", 5)),
        initial_prompt=w_cfg.get("initial_prompt", ""),
        idle_unload_minutes=int(w_cfg.get("idle_unload_minutes", 0)),
        model_registry=model_registry,
    )


def _decode_audio(data: bytes):
    """Decode audio bytes to 16 kHz mono float32 numpy array."""
    import numpy as np

    try:
        import soundfile as sf
    except ImportError:
        return _decode_wav_fallback(data)

    with io.BytesIO(data) as buf:
        audio, sr = sf.read(buf, dtype="float32", always_2d=False)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != 16000 and len(audio) > 0:
        try:
            import soxr

            audio = soxr.resample(audio, sr, 16000).astype(np.float32)
        except ImportError:
            audio = _linear_resample(audio, sr, 16000)
    return audio.astype(np.float32)


def _decode_wav_fallback(data: bytes):
    """Decode 16-, 24-, or 32-bit signed PCM WAV using stdlib wave."""
    import numpy as np

    with io.BytesIO(data) as buf, wave.open(buf, "rb") as wf:
        n_channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        sr = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    if sample_width == 2:
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif sample_width == 3:
        packed = np.frombuffer(frames, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
        values = packed[:, 0] | (packed[:, 1] << 8) | (packed[:, 2] << 16)
        values = (values ^ 0x800000) - 0x800000
        audio = values.astype(np.float32) / 8388608.0
    elif sample_width == 4:
        audio = np.frombuffer(frames, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"Unsupported WAV sample width: {sample_width}")

    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    if sr != 16000 and len(audio) > 0:
        try:
            import soxr

            audio = soxr.resample(audio, sr, 16000).astype(np.float32)
        except ImportError:
            audio = _linear_resample(audio, sr, 16000)

    return audio.astype(np.float32)


def _linear_resample(audio, source_rate: int, target_rate: int):
    """Resample mono audio with NumPy when the optional soxr backend is absent."""
    import numpy as np

    target_length = max(1, round(len(audio) * target_rate / source_rate))
    source_indices = np.arange(len(audio), dtype=np.float64)
    target_indices = np.linspace(0, len(audio) - 1, num=target_length)
    return np.interp(target_indices, source_indices, audio).astype(np.float32)


def _parse_multipart(handler: BaseHTTPRequestHandler) -> dict[str, dict]:
    """Parse multipart/form-data payload into field dictionaries."""
    ctype = handler.headers.get("Content-Type", "")
    if "multipart/form-data" not in ctype:
        raise ValueError("Expected multipart/form-data")

    boundary = None
    for part in ctype.split(";"):
        part = part.strip()
        if part.lower().startswith("boundary="):
            boundary = part.split("=", 1)[1].strip().strip('"')
            break
    if not boundary:
        raise ValueError("No boundary in Content-Type")

    length = int(handler.headers.get("Content-Length", "0"))
    if length < 0 or length > MAX_UPLOAD_BYTES:
        raise ValueError(f"Invalid/oversized payload: {length} bytes")

    raw = handler.rfile.read(length)
    sep = b"--" + boundary.encode("latin-1")
    fields = {}

    for chunk in raw.split(sep):
        chunk = chunk.strip(b"\r\n")
        if not chunk or chunk == b"--":
            continue
        try:
            header_blob, _, body = chunk.partition(b"\r\n\r\n")
            headers = {}
            for line in header_blob.split(b"\r\n"):
                if b":" in line:
                    k, v = line.split(b":", 1)
                    headers[k.strip().lower().decode("latin-1", "replace")] = v.strip().decode(
                        "latin-1", "replace"
                    )
            disp = headers.get("content-disposition", "")
            name = None
            for piece in disp.split(";"):
                piece = piece.strip()
                if piece.startswith("name="):
                    name = piece.split("=", 1)[1].strip().strip('"')
                    break
            if not name:
                continue

            body = body[:-2] if body.endswith(b"\r\n") else body
            fields[name] = {"value": body.decode("utf-8", "replace"), "data": body}
        except Exception:
            continue

    return fields


def make_handler(engine: Any):
    """Create a RequestHandler class wired to the given WhisperEngine."""
    lock = threading.Lock()

    class KuralAPIHandler(BaseHTTPRequestHandler):
        def log_message(self, fmt, *args):
            logger.debug(f"[server] {self.address_string()} {fmt % args}")

        def do_GET(self):
            route = urlsplit(self.path).path
            if route == "/health":
                self._send_json(200, {"status": "ok", "engine": "kural"})
            elif route == "/v1/models":
                self._send_json(
                    200,
                    {
                        "object": "list",
                        "data": [{"id": "whisper-1", "object": "model", "owned_by": "kural"}],
                    },
                )
            else:
                self._send_json(404, {"error": {"message": "Not found", "type": "not_found"}})

        def do_POST(self):
            if urlsplit(self.path).path != "/v1/audio/transcriptions":
                self._send_json(404, {"error": {"message": "Not found", "type": "not_found"}})
                return

            try:
                fields = _parse_multipart(self)
            except Exception as e:
                self._send_json(
                    400,
                    {"error": {"message": f"Bad multipart: {e}", "type": "invalid_request_error"}},
                )
                return

            audio_data = fields.get("file", {}).get("data")
            if not audio_data:
                self._send_json(
                    400,
                    {"error": {"message": "Missing 'file' field", "type": "invalid_request_error"}},
                )
                return

            response_format = (fields.get("response_format", {}).get("value") or "json").lower()
            language = fields.get("language", {}).get("value")
            prompt = fields.get("prompt", {}).get("value") or ""

            try:
                audio_array = _decode_audio(audio_data)
            except Exception as e:
                self._send_json(
                    400,
                    {
                        "error": {
                            "message": f"Could not decode audio: {e}",
                            "type": "invalid_request_error",
                        }
                    },
                )
                return

            with lock:
                old_lang = getattr(engine, "language", "en")
                old_prompt = getattr(engine, "initial_prompt", "")
                try:
                    if language and language != "auto":
                        engine.language = language
                    if prompt:
                        engine.initial_prompt = prompt
                    text = engine.transcribe_audio(audio_array) or ""
                finally:
                    engine.language = old_lang
                    engine.initial_prompt = old_prompt

            if response_format == "text":
                self._send_text(200, text)
            else:
                self._send_json(200, {"text": text})

        def _send_json(self, status: int, payload: dict):
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _send_text(self, status: int, body_str: str):
            data = (body_str or "").encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return KuralAPIHandler


def run_server(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT, engine: Any = None) -> int:
    """Run the OpenAI-compatible HTTP server forever."""
    print("\n🌐 Kural — Local OpenAI-Compatible Speech Server")
    print("─" * 55)

    try:
        active_engine = engine or build_server_engine()
    except Exception as e:
        print(f"❌ Could not initialize Whisper engine: {e}")
        return 1

    handler_cls = make_handler(active_engine)
    try:
        httpd = ThreadingHTTPServer((host, port), handler_cls)
    except OSError as e:
        print(f"❌ Could not bind {host}:{port} — {e}")
        return 1

    print(f"✅ Listening on http://{host}:{port}")
    print("   POST /v1/audio/transcriptions  — OpenAI-compatible Whisper endpoint")
    print("   GET  /v1/models                — Model listing")
    print("   GET  /health                   — Liveness probe")
    print("\n   Press Ctrl+C to stop.\n")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n   Shutting down server...")
        httpd.shutdown()

    return 0
