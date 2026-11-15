# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/adaptive.py
"""Local personalization and adaptive vocabulary learning.

Learns entirely on disk (%APPDATA%\\kural\\adaptive.json):
1. Word frequencies from accepted dictations, providing automatic hotwords for
   recurring domain terms and names (supporting English and Tamil Unicode words).
2. Word corrections taught by the user to fix persistent misrecognitions automatically.

Zero telemetry, 100% offline. Deleting adaptive.json resets all learned data.
"""

import json
import logging
import os
import re
import threading
from collections import Counter
from pathlib import Path

logger = logging.getLogger(__name__)

ADAPTIVE_FILE = "adaptive.json"
MAX_STORED_WORDS = 800
DEFAULT_HOTWORD_LIMIT = 30
MIN_WORD_OCCURRENCES = 3

# Common English stop words that should not consume hotword slots
STOPWORDS = frozenset(
    [
        "the",
        "and",
        "for",
        "that",
        "this",
        "with",
        "have",
        "from",
        "they",
        "will",
        "would",
        "there",
        "their",
        "what",
        "about",
        "which",
        "when",
        "make",
        "like",
        "just",
        "know",
        "take",
        "into",
        "your",
        "some",
        "could",
        "them",
        "then",
        "than",
        "been",
        "were",
        "said",
        "each",
        "she",
        "how",
        "their",
        "if",
        "we",
        "do",
        "a",
        "i",
        "is",
        "it",
        "in",
        "on",
        "at",
        "of",
        "to",
        "as",
        "be",
        "or",
        "by",
        "an",
        "so",
        "no",
        "not",
        "but",
        "was",
        "are",
        "you",
        "he",
        "his",
        "her",
        "its",
        "our",
        "out",
        "up",
        "down",
        "over",
        "under",
        "can",
        "may",
        "might",
        "must",
        "shall",
        "should",
        "did",
        "does",
        "done",
        "going",
        "go",
        "got",
        "get",
        "very",
        "really",
        "also",
        "because",
        "please",
        "thanks",
    ]
)

_PUNCT_PATTERN = re.compile(r"^[\s.,;:!?\"'()\[\]{}«»।॥`~*_\-]+|[\s.,;:!?\"'()\[\]{}«»।॥`~*_\-]+$")


def _tokenize(text: str) -> list[str]:
    """Tokenize text into candidate vocabulary words, preserving Tamil Unicode words."""
    words = []
    for raw in (text or "").split():
        clean = _PUNCT_PATTERN.sub("", raw)
        if (
            len(clean) >= 3
            and not any(c.isdigit() for c in clean)
            and clean.lower() not in STOPWORDS
        ):
            words.append(clean)
    return words


class AdaptiveLearner:
    """Maintains local word counts and corrections dictionary."""

    def __init__(self, storage_dir: str | Path | None = None, enabled: bool = True):
        from kural.engine.utils import get_user_app_data_path

        base_dir = Path(storage_dir) if storage_dir else Path(get_user_app_data_path())
        self.path = base_dir / ADAPTIVE_FILE
        self.enabled = enabled
        self._lock = threading.Lock()

        self.word_counts: Counter[str] = Counter()
        self.corrections: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            with open(self.path, encoding="utf-8") as f:
                data = json.load(f)
            self.word_counts = Counter(data.get("word_counts", {}))
            self.corrections = dict(data.get("corrections", {}))
        except Exception as e:
            logger.warning(f"Could not load adaptive data from {self.path}: {e}")

    def _save(self) -> None:
        if not self.enabled:
            return
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            # Prune to max words if needed
            pruned_counts = dict(self.word_counts.most_common(MAX_STORED_WORDS))
            tmp_path = self.path.with_suffix(".tmp")
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(
                    {"word_counts": pruned_counts, "corrections": self.corrections},
                    f,
                    ensure_ascii=False,
                    indent=2,
                )
            os.replace(tmp_path, self.path)
        except Exception as e:
            logger.warning(f"Failed to save adaptive data: {e}")

    def learn_text(self, text: str) -> None:
        """Count words from a completed dictation."""
        if not self.enabled or not text:
            return

        tokens = _tokenize(text)
        if not tokens:
            return

        with self._lock:
            for w in tokens:
                self.word_counts[w] += 1
            self._save()

    def get_adaptive_hotwords(self, limit: int = DEFAULT_HOTWORD_LIMIT) -> list[str]:
        """Return the most frequent domain-specific terms that meet the occurrence threshold."""
        with self._lock:
            candidates = [
                word
                for word, count in self.word_counts.most_common(limit * 2)
                if count >= MIN_WORD_OCCURRENCES
            ]
            return candidates[:limit]

    def teach_correction(self, original_word: str, corrected_word: str) -> None:
        """Teach a word replacement mapping."""
        orig = original_word.strip()
        corr = corrected_word.strip()
        if not orig or not corr or orig.lower() == corr.lower():
            return

        with self._lock:
            self.corrections[orig.lower()] = corr
            self._save()

    def apply_corrections(self, text: str) -> str:
        """Apply learned word-level corrections to transcribed text."""
        if not text or not self.corrections:
            return text

        with self._lock:
            # Word-boundary replacements
            for orig, corr in self.corrections.items():
                pattern = re.compile(rf"\b{re.escape(orig)}\b", re.IGNORECASE)
                text = pattern.sub(corr, text)

        return text
