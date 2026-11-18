# MIT License — Copyright (c) 2026 Kural Project
# Inspired by anomalyco/hex (docs/features/labs.md: Stop phrase)
"""Voice stop phrase detection and transcript stripping.

Allows hands-free dictations to finish automatically when the speaker says
a designated stop phrase (e.g. "stop dictation", "முடி", "stop பண்ணு") without
requiring a physical hotkey press. The matched stop phrase is automatically
stripped from the finalized transcript before typing or pasting.
"""

import logging
import re

logger = logging.getLogger(__name__)

DEFAULT_STOP_PHRASES = [
    "stop dictation",
    "stop recording",
    "முடி",
    "நிறுத்து",
    "stop பண்ணு",
]


class StopPhraseMatcher:
    """Detects spoken stop phrases in live streaming transcripts and strips them."""

    def __init__(self, enabled: bool = False, phrases: list[str] | None = None):
        self.enabled = bool(enabled)
        raw_phrases = phrases if phrases is not None else DEFAULT_STOP_PHRASES
        self.phrases = [p.strip().lower() for p in raw_phrases if p and p.strip()]

    def check_match(self, streaming_text: str) -> str | None:
        """Check if incoming interim speech text ends with any configured stop phrase.

        Returns:
            The matched canonical stop phrase string, or None if not detected.
        """
        if not self.enabled or not streaming_text:
            return None

        clean = streaming_text.strip().lower()
        # Strip trailing punctuation for robust matching
        clean = re.sub(r"[.!?,;:]+$", "", clean).strip()

        for phrase in self.phrases:
            # Word boundary check or endswith check
            pattern = rf"(?:\b|^){re.escape(phrase)}$"
            if re.search(pattern, clean):
                return phrase

        return None

    def strip_stop_phrase(self, text: str) -> str:
        """Strip any trailing stop phrase from the finalized transcript text.

        Examples:
            "Meeting starts tomorrow. Stop dictation." -> "Meeting starts tomorrow."
            "Stop dictation" -> ""
        """
        if not text:
            return ""

        result = text.strip()
        for phrase in self.phrases:
            # Match the phrase at the end, along with leading whitespace/commas and trailing punctuation
            pattern = rf"(?:\s*[,;]*\s*){re.escape(phrase)}[.!?]*\s*$"
            match = re.search(pattern, result, flags=re.IGNORECASE)
            if match:
                prefix = result[: match.start()].strip()
                result = prefix
                break

        return result
