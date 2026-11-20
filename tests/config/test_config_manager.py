"""Tests for kural.config.config_manager — fast unit tests without network or mic."""

import logging
from pathlib import Path

from kural.config.config_manager import (
    ConfigManager,
    deep_merge_config,
    validate_config,
)


class TestDeepMergeConfig:
    def test_merge_flat_dicts(self):
        default = {"a": 1, "b": 2}
        user = {"b": 3, "c": 4}
        merged = deep_merge_config(default, user)
        assert merged == {"a": 1, "b": 3, "c": 4}

    def test_merge_nested_dicts(self):
        default = {"section": {"sub": 10, "keep": True}}
        user = {"section": {"sub": 20}}
        merged = deep_merge_config(default, user)
        assert merged == {"section": {"sub": 20, "keep": True}}

    def test_user_replaces_non_dict(self):
        default = {"key": "default_value"}
        user = {"key": "user_value"}
        merged = deep_merge_config(default, user)
        assert merged["key"] == "user_value"


class TestValidateConfig:
    def test_validates_numeric_range_clamps_to_default(self):
        logger = logging.getLogger("test")
        default = {"audio": {"max_duration": 30}}
        bad_config = {"audio": {"max_duration": -5}}
        validated = validate_config(bad_config, default, logger)
        assert validated["audio"]["max_duration"] == 30

    def test_validates_theme_fallback(self):
        logger = logging.getLogger("test")
        default = {"ui": {"theme": "system"}}
        bad_config = {"ui": {"theme": "neon_rainbow"}}
        validated = validate_config(bad_config, default, logger)
        assert validated["ui"]["theme"] == "system"

    def test_hotkey_conflict_clears_auto_send(self):
        logger = logging.getLogger("test")
        default = {
            "hotkey": {
                "stop_key": "ctrl",
                "auto_send_key": "ctrl+enter",
                "recording_hotkey": "ctrl+space",
                "command_hotkey": "ctrl+shift+space",
                "recording_mode": "toggle",
            }
        }
        conflict_config = {
            "hotkey": {
                "stop_key": "ctrl",
                "auto_send_key": "ctrl",  # conflict with stop_key
                "recording_hotkey": "ctrl+space",
                "command_hotkey": "ctrl+shift+space",
                "recording_mode": "toggle",
            }
        }
        validated = validate_config(conflict_config, default, logger)
        assert validated["hotkey"]["auto_send_key"] == ""


class TestConfigManager:
    def test_loads_default_config(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        cfg = ConfigManager(quiet=True)
        whisper_cfg = cfg.get_whisper_config()
        assert whisper_cfg["model"] == "large-v3-turbo"
        assert whisper_cfg["device"] == "cuda"
        assert whisper_cfg["compute_type"] == "float16"
        assert whisper_cfg["language"] == "en"

    def test_get_audio_and_hotkey_configs(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        cfg = ConfigManager(quiet=True)
        audio = cfg.get_audio_config()
        assert "max_duration" in audio
        hotkey = cfg.get_hotkey_config()
        assert "recording_hotkey" in hotkey

    def test_malformed_user_sections_reset_to_defaults(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        cfg = ConfigManager(quiet=True)
        Path(cfg.user_settings_path).write_text(
            "audio: []\nwhisper: nope\nhotkey: {}\n", encoding="utf-8"
        )

        reloaded = ConfigManager(quiet=True)

        assert isinstance(reloaded.get_audio_config(), dict)
        assert isinstance(reloaded.get_whisper_config(), dict)
        assert reloaded.get_whisper_config()["model"] == "large-v3-turbo"

    def test_user_override_persists(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        cfg = ConfigManager(quiet=True)
        cfg.update_user_setting("whisper", "beam_size", 3)
        assert cfg.get_whisper_config()["beam_size"] == 3

        # Re-load to verify persistence
        cfg2 = ConfigManager(quiet=True)
        assert cfg2.get_whisper_config()["beam_size"] == 3
