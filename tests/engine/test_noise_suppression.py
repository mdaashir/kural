"""Tests for kural.engine.noise_suppression — spectral subtraction noise gate."""

from unittest.mock import MagicMock, patch

import numpy as np

from kural.engine.noise_suppression import apply_noise_reduction


class TestNoiseSuppression:
    def test_empty_or_none_audio_passthrough(self):
        assert apply_noise_reduction(None) is None
        empty = np.array([], dtype=np.float32)
        assert len(apply_noise_reduction(empty)) == 0

    def test_missing_library_falls_back_to_passthrough(self):
        fake_audio = np.ones(16000, dtype=np.float32) * 0.2
        with patch.dict("sys.modules", {"noisereduce": None}):
            res = apply_noise_reduction(fake_audio, sample_rate=16000, strength=0.75)
            assert np.array_equal(res, fake_audio)

    def test_successful_reduction_with_mocked_noisereduce(self):
        fake_audio = np.ones(16000, dtype=np.float32) * 0.2
        fake_nr = MagicMock()
        # Mock reduced noise array
        fake_nr.reduce_noise.return_value = fake_audio * 0.5

        with patch.dict("sys.modules", {"noisereduce": fake_nr}):
            res = apply_noise_reduction(fake_audio, sample_rate=16000, strength=0.8)
            fake_nr.reduce_noise.assert_called_once()
            call_kwargs = fake_nr.reduce_noise.call_args[1]
            assert call_kwargs["sr"] == 16000
            assert call_kwargs["prop_decrease"] == 0.8
            assert res.dtype == np.float32
            assert res.shape == fake_audio.shape

    def test_strength_clamped_between_zero_and_one(self):
        fake_audio = np.zeros(8000, dtype=np.float32)
        fake_nr = MagicMock()
        fake_nr.reduce_noise.return_value = fake_audio

        with patch.dict("sys.modules", {"noisereduce": fake_nr}):
            apply_noise_reduction(fake_audio, strength=1.5)
            assert fake_nr.reduce_noise.call_args[1]["prop_decrease"] == 1.0

            apply_noise_reduction(fake_audio, strength=-0.5)
            assert fake_nr.reduce_noise.call_args[1]["prop_decrease"] == 0.0

    def test_exception_in_library_returns_original(self):
        fake_audio = np.ones(4000, dtype=np.float32)
        fake_nr = MagicMock()
        fake_nr.reduce_noise.side_effect = RuntimeError("STFT computation error")

        with patch.dict("sys.modules", {"noisereduce": fake_nr}):
            res = apply_noise_reduction(fake_audio)
            assert np.array_equal(res, fake_audio)
