"""Tests for kural.control.media — testing volume and media transport control."""

from unittest.mock import patch

from kural.control.media import (
    VK_MEDIA_NEXT_TRACK,
    VK_MEDIA_PLAY_PAUSE,
    VK_MEDIA_PREV_TRACK,
    VK_VOLUME_MUTE,
    change_volume,
    media_next,
    media_play_pause,
    media_prev,
    set_volume,
    toggle_mute,
)


class TestVolumeControl:
    def test_release_calls_vmethod_index_2(self):
        from unittest.mock import MagicMock

        from kural.control.media import _release

        fake_ptr = MagicMock()
        with patch("kural.control.media._vmethod") as mock_vmethod:
            mock_rel = MagicMock()
            mock_vmethod.return_value = mock_rel
            _release(fake_ptr)
            mock_vmethod.assert_called_once()
            # Index 2 is IUnknown::Release
            assert mock_vmethod.call_args[0][1] == 2
            mock_rel.assert_called_once_with(fake_ptr)

    def test_get_volume_cleans_up_com_resources(self):
        from unittest.mock import MagicMock

        from kural.control.media import get_volume

        fake_pv = MagicMock()
        with (
            patch("kural.control.media._endpoint_volume", return_value=fake_pv),
            patch("kural.control.media._vmethod") as mock_vmethod,
            patch("kural.control.media._release") as mock_release,
            patch("kural.control.media._uninitialize_com") as mock_uninit,
        ):
            # Mock get_scalar (index 9) returning 0 (S_OK)
            mock_get_scalar = MagicMock(return_value=0)
            mock_vmethod.return_value = mock_get_scalar
            _ = get_volume()
            mock_release.assert_called_once_with(fake_pv)
            mock_uninit.assert_called_once()

    def test_set_volume_cleans_up_com_resources(self):
        from unittest.mock import MagicMock

        from kural.control.media import set_volume

        fake_pv = MagicMock()
        with (
            patch("kural.control.media._endpoint_volume", return_value=fake_pv),
            patch("kural.control.media._vmethod") as mock_vmethod,
            patch("kural.control.media._release") as mock_release,
            patch("kural.control.media._uninitialize_com") as mock_uninit,
        ):
            # Mock set_scalar (index 7) returning 0 (S_OK)
            mock_set_scalar = MagicMock(return_value=0)
            mock_vmethod.return_value = mock_set_scalar
            _ = set_volume(75)
            mock_release.assert_called_once_with(fake_pv)
            mock_uninit.assert_called_once()

    def test_set_volume_clamps_range(self):
        with patch("kural.control.media._endpoint_volume", return_value=None):
            # Test clamping logic without crashing when COM endpoint is None
            assert set_volume(150) == 100
            assert set_volume(-20) == 0
            assert set_volume(75) == 75

    def test_change_volume_adds_delta(self):
        with (
            patch("kural.control.media.get_volume", return_value=50),
            patch("kural.control.media.set_volume", side_effect=lambda v: max(0, min(100, v))),
        ):
            new_vol = change_volume(10)
            assert new_vol == 60

            new_vol = change_volume(-20)
            assert new_vol == 30

    def test_change_volume_defaults_if_none(self):
        with (
            patch("kural.control.media.get_volume", return_value=None),
            patch("kural.control.media.set_volume", side_effect=lambda v: max(0, min(100, v))),
        ):
            # Defaults to 50 + 10 = 60
            new_vol = change_volume(10)
            assert new_vol == 60


class TestMediaTransport:
    def test_toggle_mute_sends_vk(self):
        with patch("kural.control.media._send_vk") as mock_vk:
            toggle_mute()
            mock_vk.assert_called_once_with(VK_VOLUME_MUTE)

    def test_media_play_pause_sends_vk(self):
        with patch("kural.control.media._send_vk") as mock_vk:
            media_play_pause()
            mock_vk.assert_called_once_with(VK_MEDIA_PLAY_PAUSE)

    def test_media_next_sends_vk(self):
        with patch("kural.control.media._send_vk") as mock_vk:
            media_next()
            mock_vk.assert_called_once_with(VK_MEDIA_NEXT_TRACK)

    def test_media_prev_sends_vk(self):
        with patch("kural.control.media._send_vk") as mock_vk:
            media_prev()
            mock_vk.assert_called_once_with(VK_MEDIA_PREV_TRACK)
