"""Tests for kural.engine.utils — cross-cutting helpers, asset resolution, and relaunch."""

import sys
from pathlib import Path
from unittest.mock import patch

from kural.engine.utils import (
    OptionalComponent,
    beautify_hotkey,
    build_relaunch_command,
    get_version,
    parse_hotkey,
    resolve_asset_path,
)


class TestHotkeyHelpers:
    def test_beautify_hotkey(self):
        assert beautify_hotkey("ctrl+space") == "CTRL+SPACE"
        assert beautify_hotkey("") == ""

    def test_parse_hotkey(self):
        assert parse_hotkey("ctrl+shift+space") == ["ctrl", "shift", "space"]
        assert parse_hotkey("") == []


class TestOptionalComponent:
    def test_delegates_existing_attributes(self):
        class RealObj:
            def greet(self):
                return "hello"

        comp = OptionalComponent(RealObj())
        assert comp.greet() == "hello"

    def test_missing_attribute_returns_noop_callable(self):
        comp = OptionalComponent(None)
        res = comp.nonexistent_method(1, 2, key="val")
        assert res is None


class TestRelaunchCommand:
    def test_build_relaunch_command_uses_kural_module(self):
        cmd = build_relaunch_command(windowless=False)
        assert len(cmd) == 3
        assert cmd[1] == "-m"
        assert cmd[2] == "kural"

    def test_build_relaunch_command_frozen(self):
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "executable", "C:\\Program Files\\Kural\\kural.exe"),
        ):
            cmd = build_relaunch_command(windowless=False)
            assert cmd == ["C:\\Program Files\\Kural\\kural.exe"]


class TestAssetResolution:
    def test_resolve_asset_path_frozen(self, tmp_path):
        meipass = tmp_path / "meipass"
        cfg_dir = meipass / "kural" / "config"
        cfg_dir.mkdir(parents=True)
        defaults_file = cfg_dir / "app_rules.defaults.yaml"
        defaults_file.write_text("rules: []", encoding="utf-8")

        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "_MEIPASS", str(meipass), create=True),
        ):
            resolved = resolve_asset_path("app_rules.defaults.yaml")
            assert Path(resolved).exists()
            assert resolved == str(defaults_file)

    def test_resolve_asset_path_repo_checkout(self):
        resolved = resolve_asset_path("config.defaults.yaml")
        assert Path(resolved).exists()
        assert "config.defaults.yaml" in resolved


class TestGetVersion:
    def test_get_version_installed_distribution(self):
        with (
            patch("kural.engine.utils.is_installed_package", return_value=True),
            patch("importlib.metadata.version", return_value="9.8.7") as version,
        ):
            assert get_version() == "9.8.7"
        version.assert_called_once_with("cmd-kural")

    def test_get_version_repo_checkout(self):
        with patch("kural.engine.utils.is_installed_package", return_value=False):
            assert get_version() == "0.1.3-dev"

    def test_get_version_frozen(self, tmp_path):
        meipass = tmp_path / "meipass"
        meipass.mkdir(parents=True)
        pyproj = meipass / "pyproject.toml"
        pyproj.write_text('[project]\nname = "cmd-kural"\nversion = "0.5.0"\n', encoding="utf-8")

        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "_MEIPASS", str(meipass), create=True),
        ):
            ver = get_version()
            assert ver == "0.5.0"
