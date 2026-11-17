"""Tests for kural.engine.audio_gain — whisper mode adaptive volume boosting."""

import numpy as np

from kural.engine.audio_gain import TARGET_PEAK, boost_quiet_audio


class TestAudioGain:
    def test_empty_or_none_returns_same(self):
        assert boost_quiet_audio(None) is None
        empty = np.array([], dtype=np.float32)
        res = boost_quiet_audio(empty)
        assert res.size == 0

    def test_silence_below_noise_floor_not_boosted(self):
        # Pure silence well below SILENCE_PEAK (1e-3)
        silence = np.full(16000, 1e-5, dtype=np.float32)
        res = boost_quiet_audio(silence)
        # Untouched to avoid amplifying background hiss into hallucinations
        np.testing.assert_array_equal(res, silence)

    def test_quiet_speech_is_boosted_to_target(self):
        # Peak speech around 0.1
        quiet_audio = (np.sin(np.linspace(0, 50, 16000)) * 0.1).astype(np.float32)
        res = boost_quiet_audio(quiet_audio, max_gain=8.0)

        # Should scale up close to TARGET_PEAK (0.6)
        peak_res = float(np.percentile(np.abs(res), 99.9))
        assert peak_res > 0.55
        assert peak_res <= TARGET_PEAK + 0.05

    def test_loud_speech_untouched(self):
        # Speech already peaking at 0.8 (above TARGET_PEAK 0.6)
        loud_audio = (np.sin(np.linspace(0, 50, 16000)) * 0.8).astype(np.float32)
        res = boost_quiet_audio(loud_audio)
        # Should not scale down
        np.testing.assert_array_equal(res, loud_audio)

    def test_max_gain_limit_enforced(self):
        # Very quiet speech peaking around 0.02
        very_quiet = (np.sin(np.linspace(0, 50, 16000)) * 0.02).astype(np.float32)
        # Max gain of 4.0 -> peak should be ~0.08, capped from reaching 0.6
        res = boost_quiet_audio(very_quiet, max_gain=4.0)
        peak_res = float(np.percentile(np.abs(res), 99.9))
        assert peak_res <= 0.09

    def test_clipping_bounds_respected(self):
        audio = (np.sin(np.linspace(0, 100, 16000)) * 0.2).astype(np.float32)
        res = boost_quiet_audio(audio, max_gain=10.0)
        assert np.all(res >= -1.0)
        assert np.all(res <= 1.0)
