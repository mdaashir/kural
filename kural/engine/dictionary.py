# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/dictionary.py
"""Manages custom dictionary hotwords for biasing the Whisper speech decoder.

Allows users to add, remove, and list custom terms, technical jargon, and Tamil proper
nouns stored in `%APPDATA%\\kural\\user_settings.yaml` under `whisper.hotwords`.
"""

import logging
from pathlib import Path

from ruamel.yaml import YAML

from kural.engine.utils import get_user_app_data_path

logger = logging.getLogger(__name__)

USER_SETTINGS = "user_settings.yaml"


def _get_settings_path() -> Path:
    return Path(get_user_app_data_path()) / USER_SETTINGS


def list_hotwords(settings_path: Path | None = None) -> list[str]:
    """Return the list of custom hotwords from user_settings.yaml."""
    path = settings_path or _get_settings_path()
    if not path.exists():
        return []
    try:
        yaml = YAML()
        with open(path, encoding="utf-8") as f:
            data = yaml.load(f) or {}
        return list((data.get("whisper") or {}).get("hotwords") or [])
    except Exception as e:
        logger.warning(f"Could not read hotwords from {path}: {e}")
        return []


def add_hotword(word: str, settings_path: Path | None = None) -> bool:
    """Add a word or phrase to whisper.hotwords in user_settings.yaml."""
    clean_word = (word or "").strip()
    if not clean_word:
        return False

    path = settings_path or _get_settings_path()
    yaml = YAML()

    data = {}
    if path.exists():
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.load(f) or {}
        except Exception:
            data = {}

    whisper = data.setdefault("whisper", {})
    current = list(whisper.get("hotwords") or [])

    if clean_word in current:
        return False

    current.append(clean_word)
    whisper["hotwords"] = current

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    logger.info(f"Added '{clean_word}' to dictionary hotwords")
    return True


def remove_hotword(word: str, settings_path: Path | None = None) -> bool:
    """Remove a word or phrase from whisper.hotwords in user_settings.yaml."""
    clean_word = (word or "").strip()
    if not clean_word:
        return False

    path = settings_path or _get_settings_path()
    if not path.exists():
        return False

    yaml = YAML()
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.load(f) or {}
    except Exception:
        return False

    whisper = data.get("whisper") or {}
    current = list(whisper.get("hotwords") or [])

    if clean_word not in current:
        return False

    current.remove(clean_word)
    whisper["hotwords"] = current

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    logger.info(f"Removed '{clean_word}' from dictionary hotwords")
    return True
