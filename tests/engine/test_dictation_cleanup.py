"""Tests for kural.engine.dictation_cleanup — pure functions, no mocks needed."""

from kural.engine.dictation_cleanup import (
    apply_backtrack,
    apply_list_formatting,
    apply_lowercase,
    remove_repeated_words,
)


class TestApplyBacktrack:
    def test_simple_number_correction(self):
        result = apply_backtrack("meet at 2, actually 3")
        assert "3" in result
        assert "2" not in result
        assert "actually" not in result

    def test_no_cue_unchanged(self):
        text = "meet at 3 pm"
        assert apply_backtrack(text) == text

    def test_prose_with_cue_but_no_value_unchanged(self):
        text = "I actually like it"
        assert apply_backtrack(text) == text

    def test_empty_string(self):
        assert apply_backtrack("") == ""

    def test_cue_string_not_split(self):
        # a plain string cue must not become one cue per letter
        result = apply_backtrack("meet at 2, actually 3", cues="actually")
        assert "3" in result

    def test_empty_cues_unchanged(self):
        text = "meet at 2, actually 3"
        assert apply_backtrack(text, cues=[]) == text


class TestRemoveRepeatedWords:
    def test_simple_stutter(self):
        assert remove_repeated_words("I I think") == "I think"

    def test_triple_stutter(self):
        assert remove_repeated_words("the the the cat") == "the cat"

    def test_legit_repeat_preserved(self):
        # "very" is in _LEGIT_REPEATS
        text = "it was very very good"
        assert remove_repeated_words(text) == text

    def test_proper_noun_pair_preserved(self):
        # Capitalised copies are treated as a proper name
        assert remove_repeated_words("Walla Walla") == "Walla Walla"

    def test_empty_string(self):
        assert remove_repeated_words("") == ""

    def test_no_repeats_unchanged(self):
        text = "hello world"
        assert remove_repeated_words(text) == text

    def test_comma_stutter_at_start(self):
        # "We, we should" at start of sentence → "We should"
        result = remove_repeated_words("We, we should go")
        assert result == "We should go"


class TestApplyListFormatting:
    def test_numbered_list_two_items(self):
        text = "first, apples. second, bananas"
        result = apply_list_formatting(text)
        assert "1." in result
        assert "2." in result

    def test_bullets_style(self):
        text = "first, apples. second, bananas"
        result = apply_list_formatting(text, style="bullets")
        assert "- " in result

    def test_single_item_unchanged(self):
        text = "first, apples"
        assert apply_list_formatting(text) == text

    def test_empty_unchanged(self):
        assert apply_list_formatting("") == ""

    def test_prose_unchanged(self):
        text = "one of the two options is fine"
        assert apply_list_formatting(text) == text


class TestApplyLowercase:
    def test_capitalised_word_lowercased(self):
        assert apply_lowercase("Hello world") == "hello world"

    def test_all_caps_preserved(self):
        assert apply_lowercase("NASA launched a rocket") == "NASA launched a rocket"

    def test_mixed_case_preserved(self):
        assert apply_lowercase("I love iPhone") == "I love iPhone"

    def test_pronoun_i_preserved(self):
        assert apply_lowercase("I think") == "I think"

    def test_i_apostrophe_preserved(self):
        result = apply_lowercase("I'm here")
        assert result.startswith("I'")

    def test_protected_term_preserved(self):
        result = apply_lowercase("Hello Python", protected=["Python"])
        assert "Python" in result

    def test_empty_string(self):
        assert apply_lowercase("") == ""
