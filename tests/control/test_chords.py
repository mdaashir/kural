"""Tests for kural.control.chords — multi-key push-to-talk chord matcher."""

from kural.control.chords import (
    ChordMatcher,
    generic,
    is_chord,
    normalize,
    parse_chord,
)


class TestChordHelperFunctions:
    def test_normalize_aliases(self):
        assert normalize("control") == "ctrl"
        assert normalize("win") == "windows"
        assert normalize("cmd") == "windows"
        assert normalize("super") == "windows"
        assert normalize("option") == "alt"
        assert normalize("altgr") == "right alt"
        assert normalize("return") == "enter"
        assert normalize("ESC") == "escape"
        assert normalize("space") == "space"

    def test_generic_stripping(self):
        assert generic("left ctrl") == "ctrl"
        assert generic("right ctrl") == "ctrl"
        assert generic("left windows") == "windows"
        assert generic("right shift") == "shift"
        assert generic("space") == "space"
        assert generic("f1") == "f1"

    def test_is_chord(self):
        assert is_chord("ctrl+space") is True
        assert is_chord("ctrl+windows") is True
        assert is_chord("ctrl+alt+shift") is True
        assert is_chord("space") is False
        assert is_chord("f12") is False
        assert is_chord("") is False

    def test_parse_chord(self):
        assert parse_chord("ctrl+space") == ["ctrl", "space"]
        assert parse_chord("control + win") == ["ctrl", "windows"]
        assert parse_chord("altgr+space") == ["right alt", "space"]


class TestChordMatcherTransitions:
    def test_single_modifier_chord_press_and_release(self):
        matcher = ChordMatcher("ctrl+windows")
        assert matcher.active is False

        # First key down -> no chord yet
        assert matcher.feed("down", "left ctrl") is None
        assert matcher.active is False

        # Second key down -> chord completed!
        assert matcher.feed("down", "left windows") == "press"
        assert matcher.active is True

        # Redundant repeat while held
        assert matcher.feed("down", "left ctrl") is None
        assert matcher.active is True

        # Any key released -> chord breaks immediately!
        assert matcher.feed("up", "left ctrl") == "release"
        assert matcher.active is False

        # Releasing the second key -> stays released
        assert matcher.feed("up", "left windows") is None
        assert matcher.active is False

    def test_sided_modifier_targeting(self):
        # Targeting specifically right alt (AltGr)
        matcher = ChordMatcher("right alt+space")

        assert matcher.feed("down", "left alt") is None
        assert matcher.feed("down", "space") is None  # Left alt does not satisfy "right alt"
        assert matcher.active is False

        # Now press right alt
        assert matcher.feed("down", "right alt") == "press"
        assert matcher.active is True

        # Release space -> release transition
        assert matcher.feed("up", "space") == "release"
        assert matcher.active is False

    def test_driver_asymmetry_sided_down_generic_up(self):
        matcher = ChordMatcher("ctrl+space")

        # Down event with sided name
        assert matcher.feed("down", "left ctrl") is None
        assert matcher.feed("down", "space") == "press"
        assert matcher.active is True

        # Driver sends generic 'ctrl' key up instead of 'left ctrl'
        assert matcher.feed("up", "ctrl") == "release"
        assert matcher.active is False
        assert len(matcher.down) == 1  # only space remains
