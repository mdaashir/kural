"""Tests for kural.control.windows — mocked window management without OS side-effects."""

from unittest.mock import patch

from kural.control.windows import (
    SW_MAXIMIZE,
    SW_MINIMIZE,
    WM_CLOSE,
    WindowInfo,
    close_window,
    focus_window,
    set_window_state,
)


class TestWindowListingAndFocus:
    def test_focus_window_matches_and_brings_foreground(self):
        fake_wins = [
            WindowInfo(hwnd=1001, title="Untitled - Notepad", exe="notepad.exe"),
            WindowInfo(hwnd=1002, title="Google Chrome", exe="chrome.exe"),
        ]
        with (
            patch("kural.control.windows.list_windows", return_value=fake_wins),
            patch("ctypes.windll.user32.SwitchToThisWindow") as mock_switch,
            patch("ctypes.windll.user32.IsIconic", return_value=False),
        ):
            title = focus_window("notepad")
            assert title == "Untitled - Notepad"
            mock_switch.assert_called_once_with(1001, True)

    def test_focus_window_nonexistent_returns_none(self):
        with patch("kural.control.windows.list_windows", return_value=[]):
            assert focus_window("calculator") is None

    def test_focus_window_skips_protected_processes(self):
        fake_wins = [WindowInfo(hwnd=999, title="Task Manager", exe="Taskmgr.exe")]
        with patch("kural.control.windows.list_windows", return_value=fake_wins):
            assert focus_window("taskmgr") is None


class TestCloseWindow:
    def test_graceful_close_posts_wm_close(self):
        fake_wins = [WindowInfo(hwnd=2001, title="Document - WordPad", exe="wordpad.exe")]
        with (
            patch("kural.control.windows.list_windows", return_value=fake_wins),
            patch("ctypes.windll.user32.PostMessageW") as mock_post,
        ):
            ok, msg = close_window("wordpad")
            assert ok is True
            assert "Closing Document - WordPad" in msg
            mock_post.assert_called_once_with(2001, WM_CLOSE, 0, 0)

    def test_close_window_refuses_protected_process(self):
        ok, msg = close_window("explorer.exe")
        assert ok is False
        assert "protected" in msg

    def test_close_window_not_found(self):
        with patch("kural.control.windows.list_windows", return_value=[]):
            ok, msg = close_window("vlc")
            assert ok is False
            assert "no open window" in msg.lower()


class TestWindowState:
    def test_minimize_calls_show_window(self):
        with (
            patch("ctypes.windll.user32.GetForegroundWindow", return_value=5001),
            patch("ctypes.windll.user32.ShowWindow") as mock_show,
        ):
            ok, msg = set_window_state("minimize")
            assert ok is True
            mock_show.assert_called_once_with(5001, SW_MINIMIZE)

    def test_maximize_calls_show_window(self):
        with (
            patch("ctypes.windll.user32.GetForegroundWindow", return_value=5001),
            patch("ctypes.windll.user32.ShowWindow") as mock_show,
        ):
            ok, msg = set_window_state("maximize")
            assert ok is True
            mock_show.assert_called_once_with(5001, SW_MAXIMIZE)

    def test_snap_left_simulates_keys(self):
        with (
            patch("ctypes.windll.user32.GetForegroundWindow", return_value=5001),
            patch("ctypes.windll.user32.keybd_event") as mock_keybd,
        ):
            ok, msg = set_window_state("snap_left")
            assert ok is True
            assert mock_keybd.call_count >= 2

    def test_type_text_at_caret_calls_send_input(self):
        from kural.control.windows import type_text_at_caret

        with (
            patch("ctypes.windll.user32.SendInput") as mock_send,
            patch("kural.control.windows.check_foreground_elevation", return_value=(False, "")),
            patch("sys.platform", "win32"),
        ):
            ok = type_text_at_caret("Tamil குரல்\n")
            assert ok is True
            assert mock_send.call_count >= 10

    def test_insert_text_at_caret_fallback_on_clipboard_error(self):
        from unittest.mock import MagicMock

        from kural.control.windows import insert_text_at_caret

        fake_pyperclip = MagicMock()
        fake_pyperclip.copy.side_effect = Exception("Clipboard locked")

        with (
            patch.dict("sys.modules", {"pyperclip": fake_pyperclip}),
            patch("kural.control.windows.type_text_at_caret", return_value=True) as mock_type,
            patch("kural.control.windows.check_foreground_elevation", return_value=(False, "")),
            patch("sys.platform", "win32"),
        ):
            ok = insert_text_at_caret("Fallback test", delivery_method="paste")
            assert ok is True
            mock_type.assert_called_once_with("Fallback test")

    def test_insert_text_at_caret_copy_only(self):
        from unittest.mock import MagicMock

        from kural.control.windows import insert_text_at_caret

        fake_pyperclip = MagicMock()

        with (
            patch.dict("sys.modules", {"pyperclip": fake_pyperclip}),
            patch("kural.control.windows.type_text_at_caret") as mock_type,
        ):
            ok = insert_text_at_caret("Copy only speech", delivery_method="copy")
            assert ok is True
            fake_pyperclip.copy.assert_called_once_with("Copy only speech")
            mock_type.assert_not_called()

    def test_insert_text_at_caret_without_restore(self):
        from unittest.mock import MagicMock

        from kural.control.windows import insert_text_at_caret

        fake_pyperclip = MagicMock()
        fake_pyperclip.paste.return_value = "Prior clipboard item"

        with (
            patch.dict("sys.modules", {"pyperclip": fake_pyperclip}),
            patch("kural.control.windows.check_foreground_elevation", return_value=(False, "")),
            patch("ctypes.windll.user32.keybd_event") as mock_keybd,
            patch("threading.Thread") as mock_thread,
            patch("sys.platform", "win32"),
        ):
            ok = insert_text_at_caret(
                "Dictated text", delivery_method="paste", restore_clipboard=False
            )
            assert ok is True
            # Copied dictated text
            fake_pyperclip.copy.assert_called_once_with("Dictated text")
            # Sent Ctrl+V
            assert mock_keybd.call_count >= 4
            # Restore thread was NOT spawned
            mock_thread.assert_not_called()

    def test_get_foreground_hwnd(self):
        from kural.control.windows import get_foreground_hwnd

        with (
            patch("sys.platform", "win32"),
            patch("ctypes.windll.user32.GetForegroundWindow", return_value=12345),
        ):
            assert get_foreground_hwnd() == 12345

    def test_restore_foreground_window(self):
        from kural.control.windows import restore_foreground_window

        with (
            patch("sys.platform", "win32"),
            patch("ctypes.windll.user32.IsWindow", return_value=True),
            patch("ctypes.windll.user32.IsIconic", return_value=True),
            patch("ctypes.windll.user32.ShowWindow") as mock_show,
            patch("ctypes.windll.user32.SwitchToThisWindow") as mock_switch,
        ):
            ok = restore_foreground_window(12345, delay=0.0)
            assert ok is True
            mock_show.assert_called_once_with(12345, 9)  # SW_RESTORE = 9
            mock_switch.assert_called_once_with(12345, True)

    def test_restore_foreground_window_invalid(self):
        from kural.control.windows import restore_foreground_window

        with (
            patch("sys.platform", "win32"),
            patch("ctypes.windll.user32.IsWindow", return_value=False),
        ):
            ok = restore_foreground_window(99999, delay=0.0)
            assert ok is False
