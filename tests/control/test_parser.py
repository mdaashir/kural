"""Tests for kural.control.parser — pure intent parsing and misheard verb recovery."""

from kural.control.parser import (
    CommandIntent,
    normalize_command_text,
    parse_command,
)


class TestParserNormalization:
    def test_strips_polite_prefixes(self):
        assert normalize_command_text("please open chrome") == "open chrome"
        assert normalize_command_text("can you switch to notepad") == "switch to notepad"
        assert normalize_command_text("hey kural volume up") == "volume up"

    def test_strips_trailing_politeness(self):
        assert normalize_command_text("open edge please") == "open edge"
        assert normalize_command_text("pause music thanks") == "pause music"

    def test_repairs_misheard_verbs(self):
        # "oben" -> "open"
        assert normalize_command_text("oben notepad") == "open notepad"
        # "poen" -> "open"
        assert normalize_command_text("poen chrome") == "open chrome"
        # "swich" -> "switch to"
        assert normalize_command_text("swich edge") == "switch to edge"


class TestParserIntents:
    def test_media_intents(self):
        cmd = parse_command("play")
        assert cmd == CommandIntent(kind="media", action="play_pause", raw_text="play")

        cmd = parse_command("next song")
        assert cmd.kind == "media"
        assert cmd.action == "next"

        cmd = parse_command("mute audio")
        assert cmd.kind == "media"
        assert cmd.action == "mute"

    def test_volume_intents(self):
        cmd = parse_command("volume up")
        assert cmd.kind == "volume"
        assert cmd.action == "up"

        cmd = parse_command("decrease volume")
        assert cmd.kind == "volume"
        assert cmd.action == "down"

        cmd = parse_command("set volume to 80")
        assert cmd.kind == "volume"
        assert cmd.action == "set"
        assert cmd.target == "80"

    def test_window_state_intents(self):
        assert parse_command("minimize window").action == "minimize"
        assert parse_command("maximize window").action == "maximize"
        assert parse_command("snap window left").action == "snap_left"
        assert parse_command("snap to right").action == "snap_right"
        assert parse_command("show desktop").action == "show_desktop"

    def test_app_launch_and_switch(self):
        cmd = parse_command("open google chrome")
        assert cmd.kind == "open_app"
        assert cmd.target == "google chrome"

        cmd = parse_command("switch to visual studio code")
        assert cmd.kind == "switch_app"
        assert cmd.target == "visual studio code"

        cmd = parse_command("close notepad")
        assert cmd.kind == "close_app"
        assert cmd.target == "notepad"

    def test_web_search_intents(self):
        cmd = parse_command("search for rust tutorial")
        assert cmd.kind == "web_search"
        assert cmd.target == "rust tutorial"

        cmd = parse_command("search anirudh in youtube")
        assert cmd.kind == "web_search"
        assert cmd.action == "youtube"
        assert cmd.target == "anirudh"

    def test_system_power_intents(self):
        assert parse_command("shut down the computer").action == "shutdown"
        assert parse_command("restart the computer").action == "restart"
        assert parse_command("cancel shutdown").action == "cancel_shutdown"

    def test_unrecognized_returns_none(self):
        assert parse_command("the weather is sunny today") is None
        assert parse_command("") is None
