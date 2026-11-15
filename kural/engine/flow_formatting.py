# MIT License — Copyright (c) 2025 Rohit Burani & Mohamed Aashir S
"""Wispr Flow style natural text transformation pipeline.

Transforms raw ASR speech transcripts into clean, human-written text:
1. Strips verbal disfluencies and hesitation fillers (um, uh, er, ah, you know).
2. Collapses stuttered / false-start duplicate words ("I I think" -> "I think").
3. Translates spoken punctuation cues (English and Tamil) to actual typographic symbols.
4. Cleans punctuation spacing and ensures proper sentence capitalization.
"""

import logging
import re

logger = logging.getLogger(__name__)

# Common vocal fillers across speech
FILLER_PATTERNS = [
    re.compile(r"\b(um|uh|erm|er|ah|ahh)\b", re.IGNORECASE),
    re.compile(r"\b(you\s+know)\b", re.IGNORECASE),
]

# Stuttering / duplicate adjacent words (e.g., "I I", "we we", "the the")
DUPLICATE_WORD_PATTERN = re.compile(r"\b([a-zA-Z]+)\s+\1\b", re.IGNORECASE)

# Spoken punctuation mapping: English and Tamil triggers to symbols
SPOKEN_PUNCTUATION = [
    # Multi-word triggers first
    (re.compile(r"\s*\b(new\s+paragraph)\b\s*", re.IGNORECASE), "\n\n"),
    (re.compile(r"\s*\b(new\s+line)\b\s*", re.IGNORECASE), "\n"),
    (re.compile(r"\s*(?<!\S)(புதிய\s+வரி)(?!\S)\s*", re.IGNORECASE), "\n"),
    (re.compile(r"\b(question\s+mark)\b", re.IGNORECASE), "?"),
    (re.compile(r"\b(exclamation\s+mark|exclamation\s+point)\b", re.IGNORECASE), "!"),
    (re.compile(r"\b(full\s+stop)\b", re.IGNORECASE), "."),
    (re.compile(r"(?<!\S)(கேள்விக்குறி)(?!\S)", re.IGNORECASE), "?"),
    (re.compile(r"(?<!\S)(ஆச்சரியக்குறி)(?!\S)", re.IGNORECASE), "!"),
    # Single-word triggers
    (re.compile(r"\b(period)\b", re.IGNORECASE), "."),
    (re.compile(r"\b(comma)\b", re.IGNORECASE), ","),
    (re.compile(r"\b(colon)\b", re.IGNORECASE), ":"),
    (re.compile(r"\b(semicolon)\b", re.IGNORECASE), ";"),
    (re.compile(r"\b(dash|hyphen)\b", re.IGNORECASE), " - "),
    (re.compile(r"(?<!\S)(புள்ளி)(?!\S)", re.IGNORECASE), "."),
    (re.compile(r"(?<!\S)(கமா)(?!\S)", re.IGNORECASE), ","),
]


def strip_fillers(text: str) -> str:
    """Remove hesitation fillers and stuttered duplicate words."""
    if not text:
        return text

    # Remove vocal disfluencies
    for pat in FILLER_PATTERNS:
        text = pat.sub("", text)

    # Collapse stuttered consecutive word repetitions (run twice for triple repetitions)
    text = DUPLICATE_WORD_PATTERN.sub(r"\1", text)
    text = DUPLICATE_WORD_PATTERN.sub(r"\1", text)

    # Normalize multiple whitespace created by removals
    text = re.sub(r"[ \t]+", " ", text).strip()
    return text


def replace_spoken_punctuation(text: str) -> str:
    """Translate spoken punctuation words into real punctuation symbols."""
    if not text:
        return text

    for pat, symbol in SPOKEN_PUNCTUATION:
        text = pat.sub(symbol, text)

    return text


def format_flow_typography(text: str) -> str:
    """Clean punctuation spacing, quotes, and apply proper sentence capitalization."""
    if not text:
        return text

    # Remove spaces before punctuation marks: "word , word" -> "word, word"
    text = re.sub(r"\s+([,.:;?!])", r"\1", text)

    # Ensure space after punctuation if followed by a letter/digit: "word,word" -> "word, word"
    text = re.sub(r"([,.:;?!])([a-zA-Z0-9])", r"\1 \2", text)

    # Clean space before/after newlines
    text = re.sub(r"[ \t]*\n[ \t]*", "\n", text)

    # Capitalize first letter of every sentence
    def _capitalize_sentence(match):
        prefix = match.group(1) or ""
        char = match.group(2)
        return prefix + char.upper()

    # Match start of string or punctuation followed by space/newline
    text = re.sub(r"(^|[\.\?!]\s+|\n+)([a-z])", _capitalize_sentence, text)

    # Trim leading/trailing whitespace
    return text.strip()


def apply_flow_formatting(text: str, is_verbatim: bool = False) -> str:
    """Main pipeline to apply Wispr Flow style natural text cleanup.

    Bypasses transformations if is_verbatim is True (e.g. terminals, code editors).
    """
    if not text or is_verbatim:
        return text

    # 1. Strip disfluencies and false starts
    cleaned = strip_fillers(text)

    # 2. Translate spoken punctuation
    with_punct = replace_spoken_punctuation(cleaned)

    # 3. Clean typography and sentence capitalization
    return format_flow_typography(with_punct)
