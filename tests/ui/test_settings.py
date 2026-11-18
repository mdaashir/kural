"""Tests for kural.ui.settings_window — offline tests with mocked Tkinter."""

import sys
from unittest.mock import MagicMock, patch

from kural.ui.settings_window import (
    COMPUTE_TYPES,
    DEVICES,
    LANGUAGES,
    MODELS,
    POSITIONS,
    SettingsWindow,
    open_folder,
    open_settings_window,
)


class TestSettingsConstants:
    def test_constants_defined(self):
        assert "large-v3-turbo" in MODELS
        assert "cuda" in DEVICES
        assert "cpu" in DEVICES
        assert "float16" in COMPUTE_TYPES
        assert "ta" in LANGUAGES
        assert "bottom-center" in POSITIONS


class TestSettingsCollectionAndSave:
    def setup_method(self):
        self.mock_cm = MagicMock()
        self.mock_cm.get_whisper_config.return_value = {
            "model": "large-v3-turbo",
            "device": "cuda",
            "compute_type": "float16",
            "language": "ta",
            "idle_unload_minutes": 5,
        }
        self.mock_cm.get_hotkey_config.return_value = {
            "recording_hotkey": "ctrl+space",
            "command_hotkey": "ctrl+shift+space",
        }
        self.mock_cm.config = {
            "overlay": {"enabled": True, "position": "top-center", "click_through": True},
            "voice_commands": {"fuzzy_match": True},
        }
        self.win = SettingsWindow(config_manager=self.mock_cm)

    def test_collect_settings_default_structure(self):
        data = self.win.collect_settings()
        assert "whisper" in data
        assert "hotkey" in data
        assert "overlay" in data
        assert "voice_commands" in data
        assert "clipboard" in data
        assert "audio" in data
        assert data["audio"]["noise_suppression"]["enabled"] is False
        assert data["audio"]["ducking"]["enabled"] is False
        assert data["whisper"]["model"] == "large-v3-turbo"
        assert data["whisper"]["indic_script"] == "native"
        assert data["whisper"]["idle_unload_minutes"] == 5
        assert data["hotkey"]["recording_hotkey"] == "ctrl+space"
        assert data["hotkey"]["mouse_button"] == ""
        assert data["clipboard"]["delivery_method"] == "paste"
        assert data["overlay"]["position"] == "bottom-center"

    def test_save_invokes_set_user_setting(self):
        mock_mb = MagicMock()
        mock_callback = MagicMock()
        self.win.on_save = mock_callback

        self.win._on_save(messagebox=mock_mb)

        # Check set_user_setting calls were made
        assert self.mock_cm.set_user_setting.call_count >= 8
        self.mock_cm.set_user_setting.assert_any_call("whisper.model", "large-v3-turbo")
        self.mock_cm.set_user_setting.assert_any_call("hotkey.recording_hotkey", "ctrl+space")
        mock_mb.showinfo.assert_called_once()
        mock_callback.assert_called_once()

    def test_save_syncs_autostart_toggle(self):
        mock_mb = MagicMock()
        self.win.var_autostart = MagicMock()
        self.win.var_autostart.get.return_value = True

        with (
            patch("kural.control.autostart.is_autostart_enabled", return_value=False),
            patch("kural.control.autostart.enable_autostart") as mock_enable,
        ):
            self.win._on_save(messagebox=mock_mb)
            mock_enable.assert_called_once()

    def test_open_folder_windows(self):
        with patch.object(sys, "platform", "win32"), patch("os.startfile") as mock_start:
            open_folder("C:\\dummy\\path")
            mock_start.assert_called_once_with("C:\\dummy\\path")

    def test_open_folder_posix(self):
        with patch.object(sys, "platform", "linux"), patch("subprocess.Popen") as mock_popen:
            open_folder("/dummy/path")
            mock_popen.assert_called_once_with(["xdg-open", "/dummy/path"])


class TestOpenSettingsWindowThread:
    def test_open_settings_window_starts_thread(self):
        mock_cm = MagicMock()
        mock_cm.get_whisper_config.return_value = {}
        mock_cm.get_hotkey_config.return_value = {}
        mock_cm.config = {}

        with (
            patch("threading.Thread") as mock_thread,
            patch("threading.current_thread", return_value="worker"),
        ):
            open_settings_window(config_manager=mock_cm)
            matching_calls = [
                c for c in mock_thread.call_args_list if c[1].get("name") == "settings-ui"
            ]
            assert len(matching_calls) == 1
