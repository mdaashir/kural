"""Tests for kural.ui.fallback_window — safety net for un-deliverable dictation."""

from unittest.mock import MagicMock, patch

from kural.ui.fallback_window import FallbackWindow


class TestFallbackWindowBasics:
    def test_availability_reflects_tk(self):
        fw = FallbackWindow()
        # Tkinter is part of standard Python on Windows dev environment
        assert fw.is_available is True

    def test_empty_transcript_does_not_open_window(self):
        fw = FallbackWindow()
        with patch("threading.Thread") as mock_thread:
            fw.show("")
            fw.show("   ")
            mock_thread.assert_not_called()
            assert fw.is_open is False

    def test_show_spawns_background_thread(self):
        fw = FallbackWindow()
        with patch("threading.Thread") as mock_thread:
            mock_inst = MagicMock()
            mock_thread.return_value = mock_inst

            fw.show("Important rescued speech", reason="No text field focused")
            mock_thread.assert_called_once()
            call_kwargs = mock_thread.call_args[1]
            assert call_kwargs["target"] == fw._run_window
            assert call_kwargs["args"][0] == "Important rescued speech"
            assert call_kwargs["args"][1] == "No text field focused"
            mock_inst.start.assert_called_once()
            assert fw.is_open is True

    def test_guard_against_stacking_windows(self):
        fw = FallbackWindow()
        fw._open = True

        with patch("threading.Thread") as mock_thread:
            # Second show call while already open
            fw.show("Another dictation")
            mock_thread.assert_not_called()


class TestFallbackWindowExecution:
    def test_run_window_constructs_tk_elements_and_selects_text(self):
        fw = FallbackWindow()

        fake_tk_root = MagicMock()
        fake_text_widget = MagicMock()
        fake_pyperclip = MagicMock()

        with (
            patch("tkinter.Tk", return_value=fake_tk_root),
            patch("tkinter.Text", return_value=fake_text_widget),
            patch.dict("sys.modules", {"pyperclip": fake_pyperclip}),
        ):
            fw._run_window("Preserved sentence", "Test reason", allow_clipboard=True)

            # Verifies window setup
            fake_tk_root.title.assert_called_once_with("Kural — Dictation Captured")
            fake_text_widget.insert.assert_called_once_with("1.0", "Preserved sentence")
            # Text was pre-selected for instant Ctrl+C
            fake_text_widget.tag_add.assert_called_once_with("sel", "1.0", "end-1c")
            # Clipboard was pre-filled
            fake_pyperclip.copy.assert_called_with("Preserved sentence")
            # Mainloop ran
            fake_tk_root.mainloop.assert_called_once()
            # Lock released
            assert fw.is_open is False
