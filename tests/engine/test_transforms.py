"""Tests for kural.engine.transforms — smart voice editing and text transforms."""

from unittest.mock import MagicMock

from kural.engine.transforms import (
    apply_smart_transform,
    apply_voice_replacement,
    transform_backticks,
    transform_bullet_list,
    transform_camel_case,
    transform_code_block,
    transform_delete_last_sentence,
    transform_join_paragraph,
    transform_kebab_case,
    transform_lowercase,
    transform_numbered_list,
    transform_parentheses,
    transform_pascal_case,
    transform_quotes,
    transform_snake_case,
    transform_sort_lines,
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


class TestCodeCaseTransforms:
    def test_camel_case(self):
        assert transform_camel_case("get user profile") == "getUserProfile"
        assert transform_camel_case("hello_world_variable") == "helloWorldVariable"

    def test_pascal_case(self):
        assert transform_pascal_case("user profile component") == "UserProfileComponent"

    def test_snake_case(self):
        assert transform_snake_case("get User Profile") == "get_user_profile"

    def test_kebab_case(self):
        assert transform_kebab_case("user profile card") == "user-profile-card"


class TestWrappersAndStructuralEdits:
    def test_quotes_and_parentheses(self):
        assert transform_quotes("hello world") == '"hello world"'
        assert transform_parentheses("clarification") == "(clarification)"

    def test_code_blocks_and_backticks(self):
        assert transform_backticks("my_var") == "`my_var`"
        assert transform_code_block("print('hello')") == "```\nprint('hello')\n```"

    def test_sort_lines_alphabetical(self):
        text = "Zebra\nApple\nMango"
        res = transform_sort_lines(text)
        assert res == "Apple\nMango\nZebra"

    def test_join_paragraph(self):
        text = "Line one\nLine two\nLine three"
        assert transform_join_paragraph(text) == "Line one Line two Line three"

    def test_delete_last_sentence(self):
        text = "First sentence. Second sentence. Third sentence."
        res = transform_delete_last_sentence(text)
        assert res == "First sentence. Second sentence."


class TestVoiceReplacement:
    def test_replace_word(self):
        text = "Meeting on Monday at 3 PM"
        res, desc = apply_voice_replacement("replace Monday with Tuesday", text)
        assert res == "Meeting on Tuesday at 3 PM"
        assert "replaced 'Monday'" in desc

    def test_swap_word(self):
        text = "Let us use Python 3.11"
        res, desc = apply_voice_replacement("swap Python 3.11 for Python 3.12", text)
        assert res == "Let us use Python 3.12"

    def test_delete_word(self):
        text = "This is a very redundant phrase"
        res, desc = apply_voice_replacement("delete the word redundant", text)
        assert res == "This is a very phrase"


class TestSmartTransformDispatch:
    def test_fast_transform_bullet(self):
        res = apply_smart_transform("Point one\nPoint two", instruction="make that bullets")
        assert res == "• Point one\n• Point two"

    def test_fast_transform_title_case(self):
        res = apply_smart_transform("meeting notes", instruction="title case that")
        assert res == "Meeting Notes"

    def test_fast_transform_camel_case(self):
        res = apply_smart_transform("calculate total amount", instruction="make that camel case")
        assert res == "calculateTotalAmount"

    def test_ai_rewrite_invokes_llm(self):
        mock_llm = MagicMock()
        mock_llm.is_available.return_value = True
        mock_llm.query.return_value = "வணக்கம் உலகம்"

        res = apply_smart_transform(
            "Hello world", instruction="translate to Tamil", llm_fallback=mock_llm
        )
        assert res == "வணக்கம் உலகம்"
        mock_llm.query.assert_called_once()
