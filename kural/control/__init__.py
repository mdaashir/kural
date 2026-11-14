# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/
"""Kural voice-control subsystem: app indexing, intent parsing, window management, and execution."""

from .app_index import ALIASES, SITES, AppIndex
from .executor import CommandExecutor, CommandResult
from .guardrails import Guardrails, GuardrailsViolation, default_guardrails
from .llm_fallback import LocalLLMFallback, build_prompt, sanitize_llm_output
from .media import (
    change_volume,
    get_volume,
    media_next,
    media_play_pause,
    media_prev,
    set_volume,
    toggle_mute,
)
from .parser import CommandIntent, normalize_command_text, parse_command
from .windows import (
    WindowInfo,
    check_foreground_elevation,
    close_window,
    focus_window,
    is_window_elevated,
    list_windows,
    set_window_state,
)

__all__ = [
    "ALIASES",
    "SITES",
    "AppIndex",
    "CommandExecutor",
    "CommandIntent",
    "CommandResult",
    "Guardrails",
    "GuardrailsViolation",
    "LocalLLMFallback",
    "WindowInfo",
    "build_prompt",
    "change_volume",
    "check_foreground_elevation",
    "close_window",
    "default_guardrails",
    "focus_window",
    "get_volume",
    "is_window_elevated",
    "list_windows",
    "media_next",
    "media_play_pause",
    "media_prev",
    "normalize_command_text",
    "parse_command",
    "sanitize_llm_output",
    "set_volume",
    "set_window_state",
    "toggle_mute",
]
