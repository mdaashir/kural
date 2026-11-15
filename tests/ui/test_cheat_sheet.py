"""Tests for kural.ui.cheat_sheet — shortcuts and commands reference card."""

from unittest.mock import MagicMock, patch

from kural.ui.cheat_sheet import (
    CheatSheetWindow,
    open_cheat_sheet,
)


class TestCheatSheetData:
    def test_get_hotkey_items_default(self):
        win = CheatSheetWindow()
        items = win._get_hotkey_items()
        assert len(items) >= 2
        labels = [item[0] for item in items]
        assert "Dictation Mode" in labels
        assert "Voice Command Mode" in labels

    def test_get_hotkey_items_custom_config(self):
        mock_cm = MagicMock()
        mock_cm.get_hotkey_config.return_value = {
            "recording_hotkey": "alt+space",
            "command_hotkey": "alt+shift+space",
        }
        win = CheatSheetWindow(config_manager=mock_cm)
        items = win._get_hotkey_items()
        assert items[0][1] == "ALT+SPACE"
        assert items[1][1] == "ALT+SHIFT+SPACE"

    def test_get_voice_commands_contains_tamil_and_english(self):
        win = CheatSheetWindow()
        cmds = win._get_voice_commands()
        assert len(cmds) >= 4
        all_text = " ".join(c[1] for c in cmds)
        assert "open chrome" in all_text
        assert "திற chrome" in all_text
        assert "close notepad" in all_text

    def test_get_snippets_contains_date_time_clipboard(self):
        win = CheatSheetWindow()
        snippets = win._get_snippets()
        assert len(snippets) >= 3
        triggers = [s[1] for s in snippets]
        assert "today's date" in triggers
        assert "current time" in triggers
        assert "insert clipboard" in triggers


class TestCheatSheetWindowThread:
    def test_open_cheat_sheet_starts_daemon_thread(self):
        with (
            patch("threading.Thread") as mock_thread,
            patch("threading.current_thread", return_value="worker"),
        ):
            open_cheat_sheet()
            matching_calls = [
                c for c in mock_thread.call_args_list if c[1].get("name") == "cheat-sheet-ui"
            ]
            assert len(matching_calls) == 1
