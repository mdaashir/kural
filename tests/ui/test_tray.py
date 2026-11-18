"""Tests for kural.ui.tray — graceful degradation when pystray is unavailable."""

from unittest.mock import MagicMock

from kural.ui.tray import SystemTray


class TestSystemTrayAvailability:
    def test_disabled_tray_is_unavailable(self):
        tray = SystemTray(enabled=False)
        assert tray.is_available() is False

    def test_start_without_pystray_is_noop(self):
        tray = SystemTray(enabled=True)
        if not tray.is_available():
            tray.start()  # must not raise
            tray.stop()  # must not raise

    def test_availability_matches_pystray_presence(self):
        tray = SystemTray(enabled=True)
        expected = True
        try:
            import pystray  # noqa
        except ImportError:
            expected = False
        assert tray.is_available() is expected


class TestSystemTrayCallbacks:
    def test_callbacks_are_stored(self):
        on_dict = MagicMock()
        on_cmd = MagicMock()
        on_incog = MagicMock()
        on_hist = MagicMock()
        on_cheat = MagicMock()
        on_settings = MagicMock()
        on_exit = MagicMock()
        tray = SystemTray(
            on_toggle_dictation=on_dict,
            on_toggle_command=on_cmd,
            on_toggle_incognito=on_incog,
            is_incognito=lambda: True,
            on_open_history=on_hist,
            on_open_cheat_sheet=on_cheat,
            on_open_settings=on_settings,
            on_exit=on_exit,
        )
        assert tray.on_toggle_dictation is on_dict
        assert tray.on_toggle_command is on_cmd
        assert tray.on_toggle_incognito is on_incog
        assert tray.is_incognito() is True
        assert tray.on_open_history is on_hist
        assert tray.on_open_cheat_sheet is on_cheat
        assert tray.on_open_settings is on_settings
        assert tray.on_exit is on_exit

    def test_stop_is_safe_without_start(self):
        tray = SystemTray(enabled=False)
        tray.stop()  # must not raise
        assert tray._icon is None
