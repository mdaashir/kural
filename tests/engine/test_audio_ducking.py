"""Tests for kural.engine.audio_ducking — automatic volume ducking while dictating."""

import time
from unittest.mock import patch

from kural.engine.audio_ducking import AudioDucker


class TestAudioDuckingBasics:
    def test_disabled_by_default(self):
        ducker = AudioDucker(enabled=False)
        assert ducker.enabled is False
        # Calling start should be no-op
        with patch("kural.control.media.get_volume") as mock_get:
            ducker.start()
            mock_get.assert_not_called()

    def test_factor_clamped_between_zero_and_one(self):
        d1 = AudioDucker(enabled=True, factor=-0.5)
        assert d1.factor == 0.0

        d2 = AudioDucker(enabled=True, factor=1.8)
        assert d2.factor == 1.0


class TestAudioDuckingLifecycle:
    def test_start_lowers_volume_and_restore_returns(self):
        ducker = AudioDucker(enabled=True, factor=0.2)

        vol_levels = [80]

        def fake_get():
            return vol_levels[0]

        def fake_set(v):
            vol_levels[0] = v

        with (
            patch("kural.control.media.get_volume", side_effect=fake_get),
            patch("kural.control.media.set_volume", side_effect=fake_set),
        ):
            ducker.start()
            time.sleep(0.18)  # wait for ramp down

            # Volume should have lowered to ~20% of 80 = 16
            assert vol_levels[0] <= 20
            assert ducker._is_ducked is True

            # Restore
            ducker.restore()
            time.sleep(0.28)  # wait for ramp up

            # Volume restored back to ~80
            assert vol_levels[0] == 80
            assert ducker._is_ducked is False

    def test_start_while_already_ducked_is_noop(self):
        ducker = AudioDucker(enabled=True, factor=0.25)
        ducker._is_ducked = True

        with patch("threading.Thread") as mock_thread:
            ducker.start()
            mock_thread.assert_not_called()

    def test_restore_when_not_ducked_is_noop(self):
        ducker = AudioDucker(enabled=True, factor=0.25)
        ducker._is_ducked = False

        with patch("threading.Thread") as mock_thread:
            ducker.restore()
            mock_thread.assert_not_called()
