# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/recovery.py
"""Never-lose-a-dictation recovery: DPAPI encrypted audio take and in-memory text ledger.

LastTake keeps the single most recent recording on disk, encrypted with Windows DPAPI
(CryptProtectData) so only the current Windows user account can decrypt it. It holds exactly
one take, expires after a configurable time (default 24h), and enables retrying a failed or
interrupted dictation.

Ledger remembers the last successfully inserted text in memory, enabling voice commands
like "paste last dictation" to re-paste text into another window.
"""

import contextlib
import ctypes
import json
import logging
import os
import struct
import sys
import threading
import time

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_MAX_AGE_S = 24 * 3600
_MAGIC = b"KRL1"


if sys.platform == "win32":
    import ctypes.wintypes as wintypes

    class _DATA_BLOB(ctypes.Structure):
        _fields_ = [
            ("cbData", wintypes.DWORD),
            ("pbData", ctypes.POINTER(ctypes.c_char)),
        ]

    def _make_blob(data: bytes):
        buf = ctypes.create_string_buffer(data, len(data))
        blob = _DATA_BLOB(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
        return blob, buf

    def protect(data: bytes) -> bytes:
        """Encrypt bytes using Windows DPAPI (CryptProtectData)."""
        src_blob, _keep = _make_blob(data)
        out_blob = _DATA_BLOB()
        # CRYPTPROTECT_UI_FORBIDDEN = 0x1
        if not ctypes.windll.crypt32.CryptProtectData(
            ctypes.byref(src_blob), "Kural take", None, None, None, 0x1, ctypes.byref(out_blob)
        ):
            raise ctypes.WinError()
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

    def unprotect(data: bytes) -> bytes:
        """Decrypt bytes using Windows DPAPI (CryptUnprotectData)."""
        src_blob, _keep = _make_blob(data)
        out_blob = _DATA_BLOB()
        if not ctypes.windll.crypt32.CryptUnprotectData(
            ctypes.byref(src_blob), None, None, None, None, 0x1, ctypes.byref(out_blob)
        ):
            raise ctypes.WinError()
        try:
            return ctypes.string_at(out_blob.pbData, out_blob.cbData)
        finally:
            ctypes.windll.kernel32.LocalFree(out_blob.pbData)

else:
    # Linux / CI fallback: plain bytes or raise OSError in strict mode
    def protect(data: bytes) -> bytes:
        return b"NON_WIN_CIPHER:" + data

    def unprotect(data: bytes) -> bytes:
        if data.startswith(b"NON_WIN_CIPHER:"):
            return data[len(b"NON_WIN_CIPHER:") :]
        raise OSError("DPAPI is only available on Windows")


class LastTake:
    """Manages an encrypted single-take raw audio recording on disk."""

    def __init__(self, storage_dir: str, max_age_s: float = DEFAULT_MAX_AGE_S):
        self.path = os.path.join(storage_dir, "recovery", "last_take.bin")
        self.max_age_s = max_age_s
        self._lock = threading.Lock()

    def save(self, audio: np.ndarray, meta: dict | None = None) -> bool:
        """Encrypt and store a 16 kHz float32 recording, overwriting any previous take."""
        if audio is None or len(audio) == 0:
            return False

        pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2").tobytes()
        header_dict = {"saved": time.time(), **(meta or {})}
        header_bytes = json.dumps(header_dict).encode("utf-8")

        payload = _MAGIC + struct.pack("<I", len(header_bytes)) + header_bytes + pcm
        try:
            encrypted_blob = protect(payload)
        except Exception as e:
            logger.warning(f"Could not encrypt audio take via DPAPI: {e}")
            return False

        with self._lock:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
                tmp_path = self.path + ".tmp"
                with open(tmp_path, "wb") as f:
                    f.write(encrypted_blob)
                os.replace(tmp_path, self.path)
                return True
            except Exception as e:
                logger.warning(f"Failed to write recovery take: {e}")
                return False

    def load(self) -> tuple[np.ndarray | None, dict | None]:
        """Decrypt and load the stored take, or (None, None) if missing or expired."""
        with self._lock:
            if not os.path.exists(self.path):
                return None, None
            try:
                with open(self.path, "rb") as f:
                    raw_encrypted = f.read()
                payload = unprotect(raw_encrypted)
            except Exception as e:
                logger.warning(f"Failed to decrypt last take: {e}")
                return None, None

        if payload[:4] != _MAGIC:
            return None, None

        (header_len,) = struct.unpack("<I", payload[4:8])
        meta = json.loads(payload[8 : 8 + header_len].decode("utf-8"))

        if time.time() - meta.get("saved", 0) > self.max_age_s:
            self.clear()
            return None, None

        pcm = np.frombuffer(payload[8 + header_len :], dtype="<i2")
        audio = pcm.astype(np.float32) / 32767.0
        return audio, meta

    def exists(self) -> bool:
        return os.path.exists(self.path)

    def clear(self) -> None:
        with self._lock:
            if os.path.exists(self.path):
                with contextlib.suppress(OSError):
                    os.remove(self.path)


class Ledger:
    """Ephemeral, in-memory store of the most recently inserted dictation text."""

    def __init__(self):
        self.text = ""
        self.app = ""
        self.timestamp = 0.0
        self._lock = threading.Lock()

    def record(self, text: str, app: str = "") -> None:
        with self._lock:
            self.text = text
            self.app = app
            self.timestamp = time.time()

    def last(self) -> str:
        with self._lock:
            return self.text
