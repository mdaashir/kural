# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/snippets.py
"""Spoken shortcuts that expand inline during normal dictation.

Say "today's date" and it types the current date (YYYY-MM-DD). Supports variable
interpolation: ${date}, ${time}, and ${clipboard}. Matches longest triggers first.
"""

import functools
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

_TRAILING_PUNCT = ".,!?;:"


def _parse_snippets(snippets_list: list[dict] | None) -> tuple:
    """Normalize snippet configurations into (trigger, expansion, mode) tuples."""
    parsed = []
    for item in snippets_list or ():
        if not isinstance(item, dict):
            continue
        trigger = " ".join(str(item.get("trigger", "")).split()).lower()
        expansion = item.get("expansion")
        if not trigger or expansion is None:
            continue
        mode = str(item.get("mode", "anywhere")).lower()
        parsed.append((trigger, str(expansion), "alone" if mode == "alone" else "anywhere"))
    return tuple(parsed)


@functools.lru_cache(maxsize=16)
def _compile_pattern(triggers: tuple):
    """Compile regex matching any of the triggers, longest first."""
    if not triggers:
        return None
    sorted_triggers = sorted(triggers, key=len, reverse=True)
    parts = [r"[ \t]+".join(re.escape(w) for w in t.split()) for t in sorted_triggers]
    return re.compile(
        r"\b(?:" + "|".join(parts) + r")\b[" + re.escape(_TRAILING_PUNCT) + r"]*",
        re.IGNORECASE,
    )


def _render_variables(expansion: str) -> str:
    """Replace ${date}, ${time}, and ${clipboard} variables in the expansion."""
    if "${" not in expansion:
        return expansion

    now = datetime.now()
    rendered = expansion.replace("${date}", now.strftime("%Y-%m-%d"))
    rendered = rendered.replace("${time}", now.strftime("%H:%M"))

    if "${clipboard}" in rendered:
        clipboard_text = ""
        try:
            import pyperclip

            clipboard_text = pyperclip.paste() or ""
        except Exception as e:
            logger.debug(f"Clipboard read in snippet failed: {e}")
        rendered = rendered.replace("${clipboard}", clipboard_text)

    return rendered


def apply_snippets(text: str, snippets_config: list[dict] | None = None) -> str:
    """Expand standalone and inline spoken snippet triggers in transcribed text."""
    if not text or not snippets_config:
        return text

    parsed = _parse_snippets(snippets_config)
    if not parsed:
        return text

    normalized_text = " ".join(text.split()).lower()
    for trigger, expansion, mode in parsed:
        if mode == "alone" and normalized_text == trigger:
            return _render_variables(expansion)

    # Only anywhere-mode snippets may match as part of a larger utterance.
    mapping = {trigger: expansion for trigger, expansion, mode in parsed if mode == "anywhere"}
    pattern = _compile_pattern(tuple(mapping.keys()))
    if not pattern:
        return text

    def _replace_match(match: re.Match) -> str:
        matched_str = match.group(0).rstrip(_TRAILING_PUNCT).strip().lower()
        # Find corresponding key
        normalized_matched = " ".join(matched_str.split())
        expansion = mapping.get(normalized_matched)
        return _render_variables(expansion) if expansion is not None else match.group(0)

    return pattern.sub(_replace_match, text)
