"""Tests for kural.engine.transforms — smart voice editing and text transforms."""

from unittest.mock import MagicMock

from kural.engine.transforms import (
    apply_smart_transform,
    transform_bullet_list,
    transform_lowercase,
    transform_numbered_list,
    transform_title_case,
    transform_uppercase,
)


class TestDeterministicTransforms:
    def test_bullet_list_multiline(self):
        text = "Item one\nItem two\nItem three"
        res = transform_bullet_list(text)
        assert res == "• Item one\n• Item two\n• Item three"

    def test_bullet_list_sentences(self):
        text = "First thought. Second thought."
        res = transform_bullet_list(text)
        assert res == "• First thought.\n• Second thought."

    def test_numbered_list(self):
        text = "Step A\nStep B"
        res = transform_numbered_list(text)
        assert res == "1. Step A\n2. Step B"

    def test_title_case(self):
        text = "weekly engineering standup"
        assert transform_title_case(text) == "Weekly Engineering Standup"

    def test_uppercase_and_lowercase(self):
        assert transform_uppercase("hello world") == "HELLO WORLD"
        assert transform_lowercase("HELLO WORLD") == "hello world"


class TestSmartTransformDispatch:
    def test_fast_transform_bullet(self):
        res = apply_smart_transform("Point one\nPoint two", instruction="make that bullets")
        assert res == "• Point one\n• Point two"

    def test_fast_transform_title_case(self):
        res = apply_smart_transform("meeting notes", instruction="title case that")
        assert res == "Meeting Notes"

    def test_ai_rewrite_invokes_llm(self):
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_llm.query.return_value = "வணக்கம் உலகம்"

        res = apply_smart_transform(
            "Hello world", instruction="translate to Tamil", llm_fallback=mock_llm
        )
        assert res == "வணக்கம் உலகம்"
        mock_llm.query.assert_called_once()
