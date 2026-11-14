# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported from drajb/whisper-local/src/whisper_key/config_manager.py
"""Kural configuration subsystem: defaults layering, settings validation, and hot reload."""

from .config_manager import ConfigManager
from .defaults_merge import load_layered

__all__ = ["ConfigManager", "load_layered"]
