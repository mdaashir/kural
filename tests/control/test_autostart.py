"""Tests for kural.control.autostart — Windows registry startup management."""

import sys
from unittest.mock import MagicMock, patch

from kural.control.autostart import (
    WIN_VALUE_NAME,
    _get_windowless_python,
    build_command_string,
    build_launch_command,
    disable_autostart,
    enable_autostart,
    get_stored_autostart_command,
    is_autostart_enabled,
)


class TestAutostartCommands:
    def test_windowless_python_resolution(self, tmp_path):
        py_exe = tmp_path / "python.exe"
        py_exe.write_text("")
        pyw_exe = tmp_path / "pythonw.exe"
        pyw_exe.write_text("")

        resolved = _get_windowless_python(str(py_exe))
        assert resolved == str(pyw_exe)

    def test_windowless_python_absent_keeps_original(self, tmp_path):
        py_exe = tmp_path / "python.exe"
        py_exe.write_text("")
        resolved = _get_windowless_python(str(py_exe))
        assert resolved == str(py_exe)

    def test_build_launch_command_frozen(self):
        with (
            patch.object(sys, "frozen", True, create=True),
            patch.object(sys, "executable", "C:\\Kural\\kural.exe"),
        ):
            cmd = build_launch_command()
            assert cmd == ["C:\\Kural\\kural.exe"]

    def test_build_launch_command_unfrozen(self):
        with (
            patch.object(sys, "frozen", False, create=True),
            patch.object(sys, "platform", "win32"),
            patch.object(sys, "executable", "C:\\Python312\\python.exe"),
        ):
            cmd = build_launch_command(windowless=False)
            assert cmd == ["C:\\Python312\\python.exe", "-m", "kural"]

    def test_build_command_string_quotes_spaces(self):
        parts = ["C:\\Program Files\\Kural\\kural.exe", "--tray"]
        cmd_str = build_command_string(parts)
        assert cmd_str == '"C:\\Program Files\\Kural\\kural.exe" --tray'


class TestRegistryAutostartOps:
    def test_autostart_disabled_on_non_win32(self):
        with patch.object(sys, "platform", "linux"):
            assert is_autostart_enabled() is False
            assert enable_autostart() is False
            assert disable_autostart() is True
            assert get_stored_autostart_command() == ""

    def test_is_autostart_enabled_success(self):
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.QueryValueEx.return_value = ('"C:\\app.exe"', 1)

        with (
            patch.object(sys, "platform", "win32"),
            patch.dict("sys.modules", {"winreg": mock_winreg}),
        ):
            assert is_autostart_enabled() is True
            assert get_stored_autostart_command() == '"C:\\app.exe"'

    def test_is_autostart_enabled_missing(self):
        mock_winreg = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__.side_effect = FileNotFoundError

        with (
            patch.object(sys, "platform", "win32"),
            patch.dict("sys.modules", {"winreg": mock_winreg}),
        ):
            assert is_autostart_enabled() is False
            assert get_stored_autostart_command() == ""

    def test_enable_autostart_writes_registry(self):
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

        with (
            patch.object(sys, "platform", "win32"),
            patch.dict("sys.modules", {"winreg": mock_winreg}),
            patch(
                "kural.control.autostart.build_command_string",
                return_value='"C:\\pythonw.exe" -m kural',
            ),
        ):
            res = enable_autostart()
            assert res is True
            mock_winreg.SetValueEx.assert_called_once_with(
                mock_key,
                WIN_VALUE_NAME,
                0,
                mock_winreg.REG_SZ,
                '"C:\\pythonw.exe" -m kural',
            )

    def test_disable_autostart_deletes_value(self):
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key

        with (
            patch.object(sys, "platform", "win32"),
            patch.dict("sys.modules", {"winreg": mock_winreg}),
        ):
            res = disable_autostart()
            assert res is True
            mock_winreg.DeleteValue.assert_called_once_with(mock_key, WIN_VALUE_NAME)

    def test_disable_autostart_not_found_is_clean(self):
        mock_winreg = MagicMock()
        mock_key = MagicMock()
        mock_winreg.OpenKey.return_value.__enter__.return_value = mock_key
        mock_winreg.DeleteValue.side_effect = FileNotFoundError

        with (
            patch.object(sys, "platform", "win32"),
            patch.dict("sys.modules", {"winreg": mock_winreg}),
        ):
            assert disable_autostart() is True
