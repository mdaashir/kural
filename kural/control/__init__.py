# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/
"""Kural voice-control subsystem: app indexing, intent parsing, window management, and execution."""

from .app_index import ALIASES, SITES, AppIndex
from .executor import CommandExecutor, CommandResult
from .guardrails import Guardrails, GuardrailsViolation, default_guardrails
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
from .windows import WindowInfo, close_window, focus_window, list_windows, set_window_state

__all__ = [
    "ALIASES",
    "SITES",
    "AppIndex",
    "CommandExecutor",
    "CommandIntent",
    "CommandResult",
    "Guardrails",
    "GuardrailsViolation",
    "WindowInfo",
    "change_volume",
    "close_window",
    "default_guardrails",
    "focus_window",
    "get_volume",
    "list_windows",
    "media_next",
    "media_play_pause",
    "media_prev",
    "normalize_command_text",
    "parse_command",
    "set_volume",
    "set_window_state",
    "toggle_mute",
]
