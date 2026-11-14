"""Tests for elevated window detection in kural.control.windows — mocked token queries."""

from unittest.mock import patch

from kural.control.windows import check_foreground_elevation, is_window_elevated


class TestElevatedWindowDetection:
    def test_null_hwnd_returns_false(self):
        assert is_window_elevated(0) is False

    def test_non_elevated_window(self):
        # When token elevation value is 0 (standard user)
        with (
            patch("kural.control.windows.is_window_elevated", return_value=False),
            patch("ctypes.windll.user32.GetForegroundWindow", return_value=1234),
        ):
            is_elev, msg = check_foreground_elevation()
            assert is_elev is False
            assert msg == ""

    def test_elevated_window_detects_and_warns(self):
        # When token elevation value is 1 (Admin process like cmd or taskmgr)
        with (
            patch("kural.control.windows.is_window_elevated", return_value=True),
            patch("ctypes.windll.user32.GetForegroundWindow", return_value=5678),
        ):
            is_elev, msg = check_foreground_elevation()
            assert is_elev is True
            assert "Administrator" in msg
            assert "Windows UIPI blocks" in msg
