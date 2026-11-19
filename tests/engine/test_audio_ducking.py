"""Tests for kural.engine.audio_ducking — automatic volume ducking while dictating."""

import threading
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

    def test_restore_before_initial_volume_read_cannot_leave_audio_ducked(self):
        entered = threading.Event()
        release = threading.Event()
        levels = [80]
        ducker = AudioDucker(enabled=True, factor=0.25)

        def get_volume():
            entered.set()
            assert release.wait(2)
            return levels[0]

        def set_volume(level):
            levels[0] = level

        with (
            patch("kural.control.media.get_volume", side_effect=get_volume),
            patch("kural.control.media.set_volume", side_effect=set_volume),
        ):
            ducker.start()
            try:
                assert entered.wait(2)
                ducker.restore()
            finally:
                release.set()
            ducker._worker_thread.join(timeout=2)
            assert not ducker._worker_thread.is_alive()
            assert levels[0] == 80

    def test_stop_during_ramp_restores_original(self):
        first_write = threading.Event()
        resume = threading.Event()
        levels = [80]
        ducker = AudioDucker(enabled=True, factor=0.25)

        def set_volume(level):
            levels[0] = level
            if not first_write.is_set():
                first_write.set()
                assert resume.wait(2)

        with (
            patch("kural.control.media.get_volume", side_effect=lambda: levels[0]),
            patch("kural.control.media.set_volume", side_effect=set_volume),
        ):
            ducker.start()
            try:
                assert first_write.wait(2)
                ducker.restore()
            finally:
                resume.set()
            ducker._worker_thread.join(timeout=2)
            assert not ducker._worker_thread.is_alive()
            assert levels[0] == 80

    def test_close_waits_for_restored_volume(self):
        levels = [80]
        ducker = AudioDucker(enabled=True, factor=0.25)

        def set_volume(level):
            levels[0] = level

        with (
            patch("kural.control.media.get_volume", side_effect=lambda: levels[0]),
            patch("kural.control.media.set_volume", side_effect=set_volume),
        ):
            ducker.start()
            worker = ducker._worker_thread
            # Wait until the ramp has completed without using an arbitrary sleep.
            for _ in range(100):
                if levels[0] == 20:
                    break
                time.sleep(0.005)
            assert levels[0] == 20
            ducker.close(timeout=2)
            assert not worker.is_alive()
            assert levels[0] == 80

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
