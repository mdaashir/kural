"""Tests for kural.engine.stop_phrase — voice stop phrase detection and transcript stripping."""

from kural.engine.stop_phrase import StopPhraseMatcher


class TestStopPhraseMatcherBasics:
    def test_disabled_matcher_returns_none(self):
        matcher = StopPhraseMatcher(enabled=False)
        assert matcher.check_match("hello world stop dictation") is None

    def test_empty_string_returns_none(self):
        matcher = StopPhraseMatcher(enabled=True)
        assert matcher.check_match("") is None
        assert matcher.check_match("   ") is None

    def test_default_phrases_included(self):
        matcher = StopPhraseMatcher(enabled=True)
        assert "stop dictation" in matcher.phrases
        assert "முடி" in matcher.phrases


class TestStopPhraseMatching:
    def test_detects_english_stop_dictation(self):
        matcher = StopPhraseMatcher(enabled=True)
        assert matcher.check_match("We will release on Friday. Stop dictation.") == "stop dictation"
        assert matcher.check_match("please stop recording") == "stop recording"

    def test_detects_tamil_stop_phrases(self):
        matcher = StopPhraseMatcher(enabled=True)
        assert matcher.check_match("நாளை சந்திப்போம் முடி") == "முடி"
        assert matcher.check_match("chrome open பண்ணு stop பண்ணு") == "stop பண்ணு"

    def test_does_not_falsely_match_mid_sentence(self):
        matcher = StopPhraseMatcher(enabled=True)
        # Phrase in the middle of a sentence should not trigger
        assert matcher.check_match("Do not stop dictation because I am not done yet") is None


class TestStopPhraseStripping:
    def test_strip_trailing_phrase_and_punctuation(self):
        matcher = StopPhraseMatcher(enabled=True)
        text = "Meeting is scheduled for Monday. Stop dictation."
        stripped = matcher.strip_stop_phrase(text)
        assert stripped == "Meeting is scheduled for Monday."

    def test_strip_only_phrase_yields_empty_string(self):
        matcher = StopPhraseMatcher(enabled=True)
        text = "Stop dictation"
        stripped = matcher.strip_stop_phrase(text)
        assert stripped == ""

    def test_strip_tamil_phrase(self):
        matcher = StopPhraseMatcher(enabled=True)
        text = "வேலையை முடித்துவிட்டேன் முடி"
        stripped = matcher.strip_stop_phrase(text)
        assert stripped == "வேலையை முடித்துவிட்டேன்"
