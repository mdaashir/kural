# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/planner.py
"""Caret-aware text insertion layout planner.

Whisper returns every audio segment as a fresh sentence: capitalized with no leading
space. Dropped into the middle of an existing sentence, this reads awkwardly
(e.g., "We talked aboutThe project" instead of "We talked about the project").

When the text immediately preceding the caret is known, this planner:
- Adds a leading space when continuing words.
- Lowers the first letter for common continuation words while preserving proper nouns.
- Capitalizes new sentences following '.', '?', '!', or newlines.
- Avoids extra spaces after opening quotes/brackets or before closing punctuation.
"""

import logging
import re
from collections.abc import Iterable

logger = logging.getLogger(__name__)

# Common English words that should be lowercased when continuing a sentence mid-stream.
# Proper nouns, names, and custom dictionary words are excluded so they stay capitalized.
COMMON_WORDS = frozenset(
    [
        "a",
        "about",
        "after",
        "again",
        "all",
        "also",
        "although",
        "an",
        "and",
        "another",
        "any",
        "are",
        "as",
        "at",
        "be",
        "because",
        "been",
        "before",
        "being",
        "both",
        "but",
        "by",
        "can",
        "could",
        "did",
        "do",
        "does",
        "doing",
        "during",
        "each",
        "either",
        "even",
        "every",
        "few",
        "for",
        "from",
        "had",
        "has",
        "have",
        "having",
        "he",
        "her",
        "here",
        "hers",
        "him",
        "his",
        "how",
        "however",
        "if",
        "in",
        "into",
        "is",
        "it",
        "its",
        "just",
        "later",
        "let",
        "like",
        "maybe",
        "me",
        "more",
        "most",
        "my",
        "neither",
        "no",
        "nor",
        "not",
        "now",
        "of",
        "off",
        "on",
        "once",
        "only",
        "or",
        "other",
        "our",
        "out",
        "over",
        "perhaps",
        "please",
        "probably",
        "really",
        "she",
        "should",
        "since",
        "so",
        "some",
        "still",
        "such",
        "than",
        "that",
        "the",
        "their",
        "them",
        "then",
        "there",
        "these",
        "they",
        "this",
        "those",
        "though",
        "through",
        "thus",
        "to",
        "too",
        "under",
        "unless",
        "until",
        "up",
        "us",
        "very",
        "was",
        "we",
        "well",
        "were",
        "what",
        "when",
        "where",
        "whether",
        "which",
        "while",
        "who",
        "whom",
        "whose",
        "why",
        "will",
        "with",
        "within",
        "without",
        "would",
        "yes",
        "yet",
        "you",
        "your",
        "actually",
        "anyway",
        "basically",
        "besides",
        "finally",
        "first",
        "second",
        "third",
        "next",
        "instead",
        "meanwhile",
        "otherwise",
        "plus",
        "regardless",
        "similarly",
        "therefore",
        "today",
        "tomorrow",
        "tonight",
        "yesterday",
    ]
)

# Punctuation that attaches directly to preceding text without a leading space
_NO_SPACE_BEFORE = set(".,;:!?)]}%'’”")

# Preceding characters that take no extra trailing space before new text
_OPENERS = set("([{\"'‘“/\\-@#$₹\n\t ")

# Punctuation patterns that mark the end of a sentence
_SENTENCE_END = re.compile(r"[.!?।॥]['\")\]’”]*\s*$")


def _first_word(text: str) -> str:
    m = re.match(r"[A-Za-z][A-Za-z']*", text)
    return m.group(0) if m else ""


def plan_insertion(
    text: str,
    before: str | None,
    keep_caps: Iterable[str] = (),
) -> str:
    """Adjust dictated text formatting based on text preceding the caret.

    Args:
        text: The freshly transcribed text to insert.
        before: The characters immediately preceding the caret (or None if unknown).
        keep_caps: Specific words (e.g. custom hotwords, names) that must never be lowercased.

    Returns:
        The adjusted text with smart spacing and contextual capitalization.
    """
    if not text or before is None:
        return text

    stripped = before.rstrip(" \t")

    # 1. Capitalization: determine if we are starting a fresh sentence
    new_sentence = not stripped or stripped.endswith("\n") or bool(_SENTENCE_END.search(stripped))

    if new_sentence:
        if text[0].islower():
            text = text[0].upper() + text[1:]
    else:
        word = _first_word(text)
        keep = {k.lower() for k in keep_caps}
        if (
            word
            and word != "I"
            and not word.startswith("I'")
            and word[0].isupper()
            and word[1:] == word[1:].lower()
            and word.lower() in COMMON_WORDS
            and word.lower() not in keep
        ):
            text = text[0].lower() + text[1:]

    # 2. Spacing: join with a single space unless either side supplies one or
    # the dictation starts with closing punctuation.
    if before and before[-1] not in _OPENERS and text[0] not in _NO_SPACE_BEFORE:
        text = " " + text

    return text
