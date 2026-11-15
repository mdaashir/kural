"""Tests for kural.engine.snippets — testing inline shortcut expansion and variables."""

from datetime import datetime
from unittest.mock import MagicMock, patch

from kural.engine.snippets import _parse_snippets, _render_variables, apply_snippets


class TestSnippetParsingAndRendering:
    def test_parse_snippets_normalizes(self):
        raw = [
            {"trigger": "my email", "expansion": "user@example.com"},
            {"trigger": "  bad  spaces  ", "expansion": "clean"},
            {"invalid": "entry"},
        ]
        parsed = _parse_snippets(raw)
        assert len(parsed) == 2
        assert parsed[0] == ("my email", "user@example.com", "anywhere")
        assert parsed[1] == ("bad spaces", "clean", "anywhere")

    def test_render_variables_date_and_time(self):
        rendered = _render_variables("Today is ${date} and time is ${time}.")
        now = datetime.now()
        expected_date = now.strftime("%Y-%m-%d")
        expected_time = now.strftime("%H:%M")
        assert expected_date in rendered
        assert expected_time in rendered

    def test_render_variables_clipboard(self):
        fake_pyperclip = MagicMock()
        fake_pyperclip.paste.return_value = "https://github.com/mdaashir/kural"
        with patch.dict("sys.modules", {"pyperclip": fake_pyperclip}):
            rendered = _render_variables("Check this: ${clipboard}")
            assert "https://github.com/mdaashir/kural" in rendered


class TestApplySnippets:
    def setup_method(self):
        self.snippets_cfg = [
            {"trigger": "my signature", "expansion": "Best regards,\nMohamed Aashir"},
            {"trigger": "today's date", "expansion": "${date}"},
            {"trigger": "ping me", "expansion": "ping me on WhatsApp"},
        ]

    def test_empty_text_returns_untouched(self):
        assert apply_snippets("", self.snippets_cfg) == ""
        assert apply_snippets("hello world", []) == "hello world"

    def test_expand_snippet_inline(self):
        text = "Please reach out to me my signature."
        expanded = apply_snippets(text, self.snippets_cfg)
        assert "Best regards,\nMohamed Aashir" in expanded

    def test_expand_snippet_with_date(self):
        text = "Meeting on today's date."
        expanded = apply_snippets(text, self.snippets_cfg)
        today_str = datetime.now().strftime("%Y-%m-%d")
        assert f"Meeting on {today_str}" in expanded

    def test_longest_trigger_priority(self):
        cfg = [
            {"trigger": "work", "expansion": "Job"},
            {"trigger": "work signature", "expansion": "Work Sign"},
        ]
        text = "Here is my work signature."
        expanded = apply_snippets(text, cfg)
        assert "Work Sign" in expanded
