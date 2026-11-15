"""Tests for kural.engine.flow_formatting — Wispr Flow natural text transformations."""

from kural.engine.flow_formatting import (
    apply_flow_formatting,
    format_flow_typography,
    replace_spoken_punctuation,
    strip_fillers,
)


class TestDisfluencyStripping:
    def test_strip_vocal_fillers(self):
        text = "Um I was thinking that uh maybe we should go ah soon"
        cleaned = strip_fillers(text)
        assert cleaned == "I was thinking that maybe we should go soon"

    def test_strip_you_know(self):
        text = "This is you know a very important test"
        cleaned = strip_fillers(text)
        assert cleaned == "This is a very important test"

    def test_collapse_stuttered_repetitions(self):
        text = "I I think the the client will agree"
        cleaned = strip_fillers(text)
        assert cleaned == "I think the client will agree"

    def test_triple_stutter_collapsed(self):
        text = "we we we can do this"
        cleaned = strip_fillers(text)
        assert cleaned == "we can do this"


class TestSpokenPunctuation:
    def test_english_punctuation_replacement(self):
        text = "Hello world comma how are you question mark I am great period"
        res = replace_spoken_punctuation(text)
        assert "," in res
        assert "?" in res
        assert "." in res
        assert "comma" not in res.lower()
        assert "question mark" not in res.lower()

    def test_newline_and_paragraph(self):
        text = "First line new line second line new paragraph third line"
        res = replace_spoken_punctuation(text)
        assert res == "First line\nsecond line\n\nthird line"

    def test_tamil_spoken_punctuation(self):
        text = "வணக்கம் கமா எப்படி இருக்கிறீர்கள் கேள்விக்குறி நன்றி புள்ளி"
        res = replace_spoken_punctuation(text)
        assert format_flow_typography(res) == "வணக்கம், எப்படி இருக்கிறீர்கள்? நன்றி."


class TestFlowTypography:
    def test_spacing_around_punctuation(self):
        text = "word , another word . end"
        res = format_flow_typography(text)
        assert res == "Word, another word. End"

    def test_sentence_capitalization(self):
        text = "first sentence. second sentence? third sentence! done"
        res = format_flow_typography(text)
        assert res == "First sentence. Second sentence? Third sentence! Done"


class TestApplyFlowPipeline:
    def test_end_to_end_flow_formatting(self):
        raw = "um we should ship this tomorrow comma because uh the team is ready period"
        flow = apply_flow_formatting(raw)
        assert flow == "We should ship this tomorrow, because the team is ready."

    def test_verbatim_bypass_preserves_raw_text(self):
        raw = "git commit -m 'um fixing the bug' period"
        res = apply_flow_formatting(raw, is_verbatim=True)
        assert res == raw
