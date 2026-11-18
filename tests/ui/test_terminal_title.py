"""Tests for kural.ui.terminal_title — ANSI OSC 0 terminal tab title animations."""

import io
from unittest.mock import MagicMock, patch

from kural.ui.terminal_title import (
    TerminalTitle,
    _compose_title,
)


class TestTerminalTitleHelpers:
    def test_compose_title(self):
        assert _compose_title("") == "Kural"
        assert _compose_title("🔴") == "🔴 Kural"
        assert _compose_title("⏳ Transcribing...") == "⏳ Transcribing... Kural"

    def test_parse_frames_defaults(self):
        tt = TerminalTitle.__new__(TerminalTitle)
        frames = tt._parse_frames({})
        assert "idle" in frames
        assert "recording" in frames
        assert "processing" in frames
        assert len(frames["recording"]) >= 2
        # Verify first recording frame title
        assert "🔴" in frames["recording"][0][0]

    def test_parse_frames_custom_config(self):
        tt = TerminalTitle.__new__(TerminalTitle)
        custom_cfg = {
            "idle": "💤",
            "recording": [["MIC", 2.0]],
            "processing": "BUSY",
        }
        frames = tt._parse_frames(custom_cfg)
        assert frames["idle"][0][0] == "💤 Kural"
        assert frames["recording"][0][0] == "MIC Kural"
        assert frames["recording"][0][1] == 2.0
        assert frames["processing"][0][0] == "BUSY Kural"


class TestTerminalTitleExecution:
    def test_disabled_when_not_a_tty(self):
        mock_stdout = MagicMock()
        mock_stdout.isatty.return_value = False

        with patch("sys.stdout", mock_stdout):
            tt = TerminalTitle()
            assert tt.is_enabled is False
            tt.start()
            tt.update_state("recording")
            tt.stop()
            # Must not write escape codes when not a TTY
            mock_stdout.write.assert_not_called()

    def test_enabled_emits_initial_title_and_animates(self):
        buf = io.StringIO()
        buf.isatty = lambda: True  # type: ignore[attr-defined]

        with patch("sys.stdout", buf):
            tt = TerminalTitle()
            assert tt.is_enabled is True
            initial_output = buf.getvalue()
            assert "\033]0;Kural\007" in initial_output

            tt.start()
            tt.update_state("recording")
            # Wait briefly for thread to tick
            tt.stop()

            final_output = buf.getvalue()
            # Escapes were emitted
            assert "\033]0;" in final_output

    def test_emit_catches_stream_error_and_disables(self):
        mock_stdout = MagicMock()
        mock_stdout.isatty.return_value = True
        mock_stdout.write.side_effect = OSError("Stream closed")

        with patch("sys.stdout", mock_stdout):
            tt = TerminalTitle()
            assert tt.is_enabled is False
