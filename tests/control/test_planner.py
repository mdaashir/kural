"""Tests for kural.control.planner — caret-aware text insertion layout planning."""

import sys
from unittest.mock import MagicMock, patch

from kural.control.planner import plan_insertion
from kural.control.windows import get_text_before_caret


class TestPlanInsertion:
    def test_context_none_returns_text_untouched(self):
        text = "Hello world."
        assert plan_insertion(text, before=None) == "Hello world."

    def test_start_of_text_or_line(self):
        # Empty field starts fresh sentence (capitalized, no space)
        assert plan_insertion("hello world", before="") == "Hello world"
        assert plan_insertion("hello world", before="\n") == "Hello world"

    def test_after_sentence_end_punctuation(self):
        assert plan_insertion("we should go", before="Done.") == " We should go"
        assert plan_insertion("we should go", before="Are you ready? ") == "We should go"
        assert plan_insertion("great job", before="Awesome! ") == "Great job"

    def test_after_sentence_ending_closing_quote_or_bracket(self):
        assert plan_insertion("The next step", before='He said "Done."') == " The next step"
        assert plan_insertion("The next step", before="Finished (Done!)") == " The next step"
        assert plan_insertion("The next step", before='He said "done"') == " the next step"

    def test_mid_sentence_lowercases_common_words(self):
        # "We discussed" + "The project" -> " we discussed the project"
        res = plan_insertion("The project", before="We discussed")
        assert res == " the project"

        res = plan_insertion("Because it matters", before="I agree,")
        assert res == " because it matters"

    def test_mid_sentence_preserves_proper_nouns_and_keep_caps(self):
        # Words not in COMMON_WORDS stay capitalized
        res = plan_insertion("GitHub repository", before="Checked the")
        assert res == " GitHub repository"

        # Explicit keep_caps override
        res = plan_insertion("Kural voice assistant", before="Powered by", keep_caps=["Kural"])
        assert res == " Kural voice assistant"

        # Pronoun "I" remains capitalized
        res = plan_insertion("I think so", before="Yes,")
        assert res == " I think so"

    def test_punctuation_attaches_without_space(self):
        assert plan_insertion(", indeed", before="Yes") == ", indeed"
        assert plan_insertion(". End", before="Finished") == ". End"

    def test_openers_take_no_leading_space(self):
        assert plan_insertion("parenthetical comment", before="(") == "parenthetical comment"
        assert plan_insertion("quoted speech", before='"') == "quoted speech"
        assert plan_insertion("bracketed item", before="[") == "bracketed item"


class TestGetTextBeforeCaret:
    def test_returns_none_on_non_windows(self):
        with patch.object(sys, "platform", "linux"):
            assert get_text_before_caret() is None

    def test_returns_none_for_password_fields(self):
        mock_user32 = MagicMock()
        mock_user32.GetForegroundWindow.return_value = 1234
        mock_user32.GetWindowThreadProcessId.return_value = 1
        mock_user32.GetGUIThreadInfo.return_value = True
        # Style with ES_PASSWORD (0x0020) bit set
        mock_user32.GetWindowLongW.return_value = 0x0020

        with (
            patch.object(sys, "platform", "win32"),
            patch("ctypes.windll.user32", mock_user32, create=True),
        ):
            assert get_text_before_caret() is None
