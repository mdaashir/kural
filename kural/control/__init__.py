# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/
"""Kural voice-control subsystem: app indexing, safety guardrails, and media automation."""

from .app_index import ALIASES, SITES, AppIndex
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

__all__ = [
    "ALIASES",
    "SITES",
    "AppIndex",
    "Guardrails",
    "GuardrailsViolation",
    "change_volume",
    "default_guardrails",
    "get_volume",
    "media_next",
    "media_play_pause",
    "media_prev",
    "set_volume",
    "toggle_mute",
]
