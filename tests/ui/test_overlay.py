"""Tests for kural.ui.overlay — 100% offline, no display server required."""

from unittest.mock import MagicMock, patch

from kural.ui.overlay import LevelOverlay


class TestLevelOverlayAvailability:
    def test_disabled_overlay_is_unavailable(self):
        overlay = LevelOverlay(enabled=False)
        assert overlay.is_available() is False

    def test_tkinter_available_on_this_platform(self):
        overlay = LevelOverlay(enabled=True)
        # Tkinter ships with CPython on Windows; availability reflects that.
        assert isinstance(overlay.is_available(), bool)

    def test_start_without_tk_is_noop(self):
        overlay = LevelOverlay(enabled=False)
        overlay.start()  # must not raise
        overlay.stop()  # must not raise


class TestLevelOverlayStateCommands:
    def setup_method(self):
        self.overlay = LevelOverlay(enabled=True)
        self.overlay._running = True
        self.overlay._root = MagicMock()
        self.overlay._canvas = MagicMock()
        self.overlay._text_item = "text"
        self.overlay._wave_bars = [1, 2, 3, 4, 5, 6, 7]

    def test_show_recording_sets_mode(self):
        self.overlay._set_mode("dictation")
        assert self.overlay._mode == "dictation"

    def test_show_command_sets_mode(self):
        self.overlay._set_mode("command")
        assert self.overlay._mode == "command"

    def test_show_processing_sets_mode(self):
        self.overlay._set_mode("processing")
        assert self.overlay._mode == "processing"

    def test_hide_resets_to_hidden(self):
        self.overlay._set_mode("dictation")
        self.overlay._set_mode("hidden")
        assert self.overlay._mode == "hidden"

    def test_flash_sets_mode_and_message(self):
        self.overlay._flash(LevelOverlay.LEVEL_COLOR, "Done")
        assert self.overlay._mode == "flash"

    def test_waveform_animation_dictation(self):
        self.overlay._mode = "dictation"
        self.overlay._animate_waveform()
        assert self.overlay._canvas.coords.call_count == 7
        assert self.overlay._canvas.itemconfig.call_count == 7

    def test_waveform_animation_processing(self):
        self.overlay._mode = "processing"
        self.overlay._animate_waveform()
        assert self.overlay._canvas.coords.call_count == 7
        assert self.overlay._canvas.itemconfig.call_count == 7

    def test_public_api_queues_commands(self):
        with patch.object(self.overlay, "_dispatch") as mock_dispatch:
            self.overlay.show_recording(is_command=True)
            self.overlay.show_processing()
            self.overlay.flash_success("ok")
            self.overlay.flash_error("bad")
            self.overlay.hide()
            assert mock_dispatch.call_count == 5


class TestLevelOverlayLevelProvider:
    def test_level_provider_used_for_meter(self):
        levels = iter([0.5, 0.0])
        overlay = LevelOverlay(level_provider=lambda: next(levels), enabled=True)
        assert overlay.level_provider() == 0.5
        assert overlay.level_provider() == 0.0
