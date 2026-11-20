"""Tests for kural.engine.recovery — DPAPI encryption, expiration, and in-memory ledger."""

import time

import numpy as np

from kural.engine.recovery import LastTake, Ledger, protect, unprotect


class TestCryptoWrappers:
    def test_protect_and_unprotect_roundtrip(self):
        sample_bytes = b"Hello Kural encrypted speech take 12345"
        encrypted = protect(sample_bytes)
        assert encrypted != sample_bytes
        decrypted = unprotect(encrypted)
        assert decrypted == sample_bytes


class TestLastTakeStorage:
    def test_save_and_load_roundtrip(self, tmp_path):
        take = LastTake(storage_dir=str(tmp_path), max_age_s=60)
        assert take.exists() is False

        audio = np.linspace(-0.5, 0.5, 16000, dtype=np.float32)
        saved = take.save(audio, meta={"lang": "ta"})
        assert saved is True
        assert take.exists() is True

        loaded_audio, meta = take.load()
        assert loaded_audio is not None
        assert meta["lang"] == "ta"
        assert len(loaded_audio) == len(audio)
        # Verify audio PCM numerical fidelity
        np.testing.assert_allclose(loaded_audio, audio, atol=1e-3)

    def test_empty_audio_not_saved(self, tmp_path):
        take = LastTake(storage_dir=str(tmp_path))
        assert take.save(np.array([], dtype=np.float32)) is False

    def test_corrupt_decrypted_metadata_clears_take(self, tmp_path):
        from unittest.mock import patch

        from kural.engine.recovery import _MAGIC

        take = LastTake(storage_dir=str(tmp_path), max_age_s=60)
        assert take.save(np.zeros(16000, dtype=np.float32)) is True
        malformed_payload = _MAGIC + (100).to_bytes(4, "little") + b'{"saved":'

        with patch("kural.engine.recovery.unprotect", return_value=malformed_payload):
            loaded_audio, metadata = take.load()

        assert loaded_audio is None
        assert metadata is None
        assert take.exists() is False

    def test_expired_take_returns_none(self, tmp_path):
        take = LastTake(storage_dir=str(tmp_path), max_age_s=0.1)
        audio = np.zeros(16000, dtype=np.float32)
        take.save(audio, meta={"saved": time.time() - 100})
        loaded_audio, meta = take.load()
        assert loaded_audio is None
        assert meta is None

    def test_clear_removes_file(self, tmp_path):
        take = LastTake(storage_dir=str(tmp_path))
        audio = np.zeros(16000, dtype=np.float32)
        take.save(audio)
        assert take.exists() is True
        take.clear()
        assert take.exists() is False


class TestLedger:
    def test_record_and_retrieve_last(self):
        ledger = Ledger()
        assert ledger.last() == ""

        ledger.record("First dictation text", app="notepad")
        assert ledger.last() == "First dictation text"

        ledger.record("Second dictation paragraph", app="code")
        assert ledger.last() == "Second dictation paragraph"
