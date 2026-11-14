"""Tests for kural.engine.dictation_languages — pure functions, no mocks needed."""

from kural.engine.dictation_languages import (
    LANGUAGE_NAMES,
    OUTSIDER_CONFIDENCE,
    choose_language,
    language_name,
    normalize_languages,
)


class TestLanguageName:
    def test_known_code_returns_name(self):
        assert language_name("en") == "English"
        assert language_name("ta") == "Tamil"
        assert language_name("fr") == "French"

    def test_unknown_code_returns_code(self):
        assert language_name("xx") == "xx"
        assert language_name("zz") == "zz"

    def test_tamil_in_names(self):
        assert "ta" in LANGUAGE_NAMES
        assert LANGUAGE_NAMES["ta"] == "Tamil"


class TestNormalizeLanguages:
    def test_none_returns_empty(self):
        assert normalize_languages(None) == []

    def test_string_comma_separated(self):
        assert normalize_languages("en, ta") == ["en", "ta"]

    def test_string_space_separated(self):
        assert normalize_languages("en ta fr") == ["en", "ta", "fr"]

    def test_list_input(self):
        assert normalize_languages(["en", "ta"]) == ["en", "ta"]

    def test_drops_auto(self):
        assert normalize_languages("auto en") == ["en"]

    def test_drops_duplicates_keeps_order(self):
        assert normalize_languages("en ta en") == ["en", "ta"]

    def test_drops_blanks(self):
        assert normalize_languages("en  ta") == ["en", "ta"]

    def test_uppercased_input_lowercased(self):
        assert normalize_languages("EN TA") == ["en", "ta"]

    def test_rejects_too_long_code(self):
        assert normalize_languages("english") == []

    def test_rejects_single_char(self):
        assert normalize_languages("e") == []


class TestChooseLanguage:
    def test_empty_allowed_returns_none_none(self):
        lang, outsider = choose_language({"en": 0.9}, [])
        assert lang is None
        assert outsider is None

    def test_single_allowed_always_chosen(self):
        lang, outsider = choose_language({"ta": 0.8, "en": 0.9}, ["ta"])
        assert lang == "ta"

    def test_picks_highest_probability_from_allowed(self):
        probs = {"en": 0.6, "ta": 0.3, "fr": 0.1}
        lang, _ = choose_language(probs, ["en", "ta"])
        assert lang == "en"

    def test_outsider_detected_when_above_threshold(self):
        probs = {"de": OUTSIDER_CONFIDENCE + 0.01, "en": 0.1}
        _, outsider = choose_language(probs, ["en"])
        assert outsider == "de"

    def test_outsider_none_when_below_threshold(self):
        probs = {"de": OUTSIDER_CONFIDENCE - 0.01, "en": 0.1}
        _, outsider = choose_language(probs, ["en"])
        assert outsider is None

    def test_outsider_none_when_top_is_in_allowed(self):
        probs = {"en": 0.9, "ta": 0.1}
        _, outsider = choose_language(probs, ["en", "ta"])
        assert outsider is None

    def test_empty_probabilities(self):
        lang, outsider = choose_language({}, ["en"])
        assert lang == "en"
        assert outsider is None
