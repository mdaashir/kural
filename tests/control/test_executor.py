"""Tests for kural.control.executor — command resolution hierarchy and integration."""

from unittest.mock import MagicMock, patch

from kural.control.app_index import AppIndex
from kural.control.executor import CommandExecutor
from kural.control.guardrails import Guardrails


class TestCommandExecutor:
    def setup_method(self):
        self.mock_app_index = MagicMock(spec=AppIndex)
        self.mock_guardrails = MagicMock(spec=Guardrails)
        self.mock_guardrails.check_command_safety.return_value = (True, "")

        with patch("kural.control.executor.load_layered", return_value=([], {})):
            self.executor = CommandExecutor(
                app_index=self.mock_app_index,
                guardrails=self.mock_guardrails,
                commands_yaml_path="dummy.yaml",
            )
        # Inject sample yaml commands
        self.executor._user_commands = [
            {"trigger": "my custom command", "run": "echo hello"},
            {"trigger": "undo", "hotkey": "ctrl+z"},
        ]

    def test_hierarchy_tier_1_user_yaml_match(self):
        with patch("subprocess.Popen") as mock_popen:
            res = self.executor.execute("please run my custom command now")
            assert res.success is True
            assert res.action_type == "yaml_run"
            mock_popen.assert_called_once()

    def test_hierarchy_tier_2_guardrails_blocks_destructive(self):
        self.mock_guardrails.check_command_safety.return_value = (
            False,
            "Blocked: File deletion not permitted",
        )
        res = self.executor.execute("delete file secrets.txt")
        assert res.success is False
        assert res.action_type == "blocked"
        assert "File deletion" in res.feedback

    def test_hierarchy_tier_3_builtin_media_command(self):
        with patch("kural.control.executor.media_play_pause") as mock_media:
            res = self.executor.execute("pause")
            assert res.success is True
            assert res.action_type == "media"
            mock_media.assert_called_once()

    def test_hierarchy_tier_3_builtin_volume_command(self):
        with patch("kural.control.executor.change_volume", return_value=70) as mock_vol:
            res = self.executor.execute("volume up")
            assert res.success is True
            assert res.action_type == "volume"
            mock_vol.assert_called_once_with(10)

    def test_hierarchy_tier_3_builtin_window_op(self):
        with patch(
            "kural.control.executor.set_window_state", return_value=(True, "Minimized window")
        ) as mock_win:
            res = self.executor.execute("minimize window")
            assert res.success is True
            assert res.action_type == "window_op"
            mock_win.assert_called_once_with("minimize")

    def test_hierarchy_tier_3_app_launch_switch_if_open(self):
        # If open, switch_to focuses it
        with patch("kural.control.executor.focus_window", return_value="Google Chrome"):
            res = self.executor.execute("open chrome")
            assert res.success is True
            assert res.action_type == "open_app"
            assert "Switched to Google Chrome" in res.feedback

    def test_hierarchy_tier_3_app_launch_new_if_closed(self):
        with patch("kural.control.executor.focus_window", return_value=None):
            self.mock_app_index.find_app.return_value = ("C:\\Path\\notepad.exe", "notepad")
            self.mock_app_index.launch.return_value = True

            res = self.executor.execute("open notepad")
            assert res.success is True
            assert res.action_type == "open_app"
            assert "Opening Notepad" in res.feedback

    def test_hierarchy_tier_3_web_search(self):
        with patch("webbrowser.open") as mock_web:
            res = self.executor.execute("search for python dataclasses")
            assert res.success is True
            assert res.action_type == "web_search"
            mock_web.assert_called_once()

    def test_hierarchy_tier_4_direct_app_name(self):
        with patch("kural.control.executor.focus_window", return_value=None):
            self.mock_app_index.find_app.return_value = ("calc", "calculator")
            self.mock_app_index.launch.return_value = True

            # Just saying the app name without "open"
            res = self.executor.execute("calculator")
            assert res.success is True
            assert "Opening Calculator" in res.feedback

    def test_hierarchy_tier_5_unrecognized_returns_failure(self):
        self.mock_app_index.find_app.return_value = None
        res = self.executor.execute("the quick brown fox jumps")
        assert res.success is False
        assert res.action_type == "unrecognized"
        assert "Command not understood" in res.feedback
