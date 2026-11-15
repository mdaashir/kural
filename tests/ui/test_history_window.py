"""Tests for kural.ui.history_window — offline tests with mocked Tkinter."""

from unittest.mock import MagicMock, patch

from kural.ui.history_window import (
    HistoryWindow,
    open_history_window,
)


class TestHistoryWindowInit:
    def test_init_properties(self, tmp_path):
        win = HistoryWindow(storage_dir=tmp_path)
        assert win.WIDTH == 700
        assert win.HEIGHT == 520
        assert win.storage_dir == tmp_path
        assert win._entries == []


class TestHistoryWindowRefreshAndCopy:
    def setup_method(self):
        self.win = HistoryWindow()
        self.win.tree = MagicMock()
        self.win.status_label = MagicMock()
        self.win.search_var = MagicMock()
        self.win.search_var.get.return_value = "hello"

    @patch("kural.engine.history.search_history")
    def test_refresh_entries_populates_tree(self, mock_search):
        mock_search.return_value = [
            {
                "ts": "2026-11-15T10:00:00",
                "task": "transcribe",
                "app": "code.exe",
                "text": "hello world",
            },
            {"ts": "2026-11-15T10:05:00", "task": "command", "app": "", "text": "hello kural"},
        ]
        self.win.tree.get_children.return_value = ["row0"]

        self.win._refresh_entries()

        # Tree old rows deleted
        self.win.tree.delete.assert_called_once_with("row0")
        # 2 new rows inserted
        assert self.win.tree.insert.call_count == 2
        assert len(self.win._entries) == 2
        self.win.status_label.config.assert_called()

    def test_copy_selected_copies_to_clipboard(self):
        self.win._entries = [
            {"text": "Dictated sentence to be copied"},
        ]
        self.win.tree.selection.return_value = ["0"]

        mock_on_copy = MagicMock()
        self.win.on_copy = mock_on_copy
        mock_root = MagicMock()
        self.win.root = mock_root

        with patch.object(self.win, "_copy_to_clipboard", return_value=True) as mock_clip:
            self.win._copy_selected()
            mock_clip.assert_called_once_with("Dictated sentence to be copied")
            mock_on_copy.assert_called_once_with("Dictated sentence to be copied")
            self.win.status_label.config.assert_called()

    def test_copy_selected_no_selection_noop(self):
        self.win._entries = [{"text": "Sample"}]
        self.win.tree.selection.return_value = []

        with patch.object(self.win, "_copy_to_clipboard") as mock_clip:
            self.win._copy_selected()
            mock_clip.assert_not_called()

    def test_copy_to_clipboard_root_fallback(self):
        mock_root = MagicMock()
        self.win.root = mock_root
        res = self.win._copy_to_clipboard("test text")
        assert res is True
        mock_root.clipboard_clear.assert_called_once()
        mock_root.clipboard_append.assert_called_once_with("test text")


class TestOpenHistoryWindowThread:
    def test_open_history_window_starts_daemon_thread(self):
        with (
            patch("threading.Thread") as mock_thread,
            patch("threading.current_thread", return_value="worker"),
        ):
            open_history_window()
            matching_calls = [
                c for c in mock_thread.call_args_list if c[1].get("name") == "history-ui"
            ]
            assert len(matching_calls) == 1
