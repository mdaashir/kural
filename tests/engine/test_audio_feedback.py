"""Tests for kural.engine.audio_feedback — offline tests with mocked winsound."""

import sys
from unittest.mock import MagicMock, patch

from kural.engine.audio_feedback import AudioFeedback


class TestAudioFeedbackInitialization:
    def test_disabled_by_default_toggle(self):
        af = AudioFeedback(enabled=False)
        assert af.enabled is False

    def test_resolve_path_nonexistent_returns_empty(self):
        af = AudioFeedback()
        assert af._resolve_path("nonexistent_sound_xyz.wav") == ""

    def test_resolve_path_existing_returns_path(self, tmp_path):
        dummy_wav = tmp_path / "test.wav"
        dummy_wav.write_bytes(b"RIFFdummyWAVE")
        af = AudioFeedback()
        assert af._resolve_path(str(dummy_wav)) == str(dummy_wav)


class TestAudioFeedbackPlaybackCalls:
    def setup_method(self):
        self.af = AudioFeedback(enabled=True)

    def test_play_start_dispatches_async(self):
        with patch.object(self.af, "_play_async") as mock_async:
            self.af.play_start()
            mock_async.assert_called_once()

    def test_play_stop_dispatches_async(self):
        with patch.object(self.af, "_play_async") as mock_async:
            self.af.play_stop()
            mock_async.assert_called_once()

    def test_play_complete_dispatches_async(self):
        with patch.object(self.af, "_play_async") as mock_async:
            self.af.play_complete()
            mock_async.assert_called_once()

    def test_play_error_dispatches_async(self):
        with patch.object(self.af, "_play_async") as mock_async:
            self.af.play_error()
            mock_async.assert_called_once()

    def test_disabled_does_not_dispatch(self):
        af = AudioFeedback(enabled=False)
        with patch("threading.Thread") as mock_thread:
            af.play_start()
            af.play_stop()
            af.play_complete()
            af.play_error()
            mock_thread.assert_not_called()


class TestWinsoundIntegration:
    def test_play_sound_custom_wav(self, tmp_path):
        dummy_wav = tmp_path / "custom.wav"
        dummy_wav.write_bytes(b"RIFFdummyWAVE")
        af = AudioFeedback(enabled=True, start_sound=str(dummy_wav))

        fake_winsound = MagicMock()
        fake_winsound.SND_FILENAME = 0x00020000
        fake_winsound.SND_NODEFAULT = 0x00000002

        with (
            patch.object(sys, "platform", "win32"),
            patch.dict("sys.modules", {"winsound": fake_winsound}),
        ):
            af._play_sound(str(dummy_wav), "SystemAsterisk", 0x40)
            fake_winsound.PlaySound.assert_called_once_with(
                str(dummy_wav), fake_winsound.SND_FILENAME | fake_winsound.SND_NODEFAULT
            )

    def test_play_sound_system_alias(self):
        af = AudioFeedback(enabled=True)
        fake_winsound = MagicMock()
        fake_winsound.SND_ALIAS = 0x00010000
        fake_winsound.SND_NODEFAULT = 0x00000002

        with (
            patch.object(sys, "platform", "win32"),
            patch.dict("sys.modules", {"winsound": fake_winsound}),
        ):
            # cue_name="" tests fallback to alias
            af._play_sound("", "SystemAsterisk", 0x40, cue_name="")
            fake_winsound.PlaySound.assert_called_once_with(
                "SystemAsterisk", fake_winsound.SND_ALIAS | fake_winsound.SND_NODEFAULT
            )

    def test_play_sound_posix_noop(self):
        af = AudioFeedback(enabled=True)
        with patch.object(sys, "platform", "linux"):
            af._play_sound("", "SystemAsterisk", 0x40)  # must not raise
