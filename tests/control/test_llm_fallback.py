"""Tests for kural.control.llm_fallback — testing prompt construction, sanitization, and execution."""

import time
from unittest.mock import patch

from kural.control.llm_fallback import (
    LocalLLMFallback,
    build_prompt,
    sanitize_llm_output,
)


class TestPromptAndSanitization:
    def test_build_prompt_includes_system_instructions(self):
        prompt = build_prompt("can you turn the volume up a bit")
        assert "can you turn the volume up a bit" in prompt
        assert "Reply with ONLY the canonical command" in prompt

    def test_sanitize_clean_command(self):
        assert sanitize_llm_output("open chrome") == "open chrome"
        assert sanitize_llm_output("volume up.") == "volume up"

    def test_sanitize_command_prefix(self):
        assert sanitize_llm_output("Command: close notepad") == "close notepad"
        assert sanitize_llm_output("Canonical Command: mute") == "mute"
        assert sanitize_llm_output("reply: maximize window") == "maximize window"

    def test_sanitize_markdown_fences(self):
        assert sanitize_llm_output("```\nplay\n```") == "play"
        assert sanitize_llm_output("`switch to edge`") == "switch to edge"

    def test_sanitize_none_and_empty(self):
        assert sanitize_llm_output("NONE") is None
        assert sanitize_llm_output("none") is None
        assert sanitize_llm_output("") is None
        assert sanitize_llm_output("   ") is None


class TestLocalLLMFallbackExecution:
    def test_disabled_by_default(self):
        fallback = LocalLLMFallback(model_path="")
        assert fallback.is_available() is False
        assert fallback.resolve_command("hello") is None

    def test_resolve_command_with_mock_generator(self):
        fallback = LocalLLMFallback(model_path="dummy_model.gguf", enabled=True)
        # Mock availability and session callable
        fallback._session = lambda p: "Command: volume up"

        with patch("os.path.exists", return_value=True):
            assert fallback.is_available() is True
            canonical = fallback.resolve_command("make the music louder")
            assert canonical == "volume up"

    def test_resolve_command_timeout(self):
        fallback = LocalLLMFallback(model_path="dummy_model.gguf", timeout_sec=0.1, enabled=True)

        def slow_generator(p):
            time.sleep(0.5)
            return "volume up"

        fallback._session = slow_generator

        with patch("os.path.exists", return_value=True):
            canonical = fallback.resolve_command("slow command")
            assert canonical is None

    def test_resolve_command_none_response(self):
        fallback = LocalLLMFallback(model_path="dummy_model.gguf", enabled=True)
        fallback._session = lambda p: "NONE"

        with patch("os.path.exists", return_value=True):
            canonical = fallback.resolve_command("what is the meaning of life")
            assert canonical is None
