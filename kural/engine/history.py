# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/history.py
"""Dictation history recording, BM25 full-text search, and productivity statistics.

Stores dictation and command logs locally in `%APPDATA%\\kural\\history.jsonl`.
Provides dependency-free BM25 full-text ranking over past speech and calculates
productivity metrics: words dictated, speaking speed in WPM, time saved compared
to manual typing, and daily streak. Zero telemetry, 100% private.
"""

import contextlib
import datetime
import json
import logging
import math
import re
import threading
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

HISTORY_FILE = "history.jsonl"
DEFAULT_TYPING_WPM = 40  # standard baseline for time saved calculation


@dataclass
class HistoryEntry:
    """Record of a single dictation or voice command."""

    text: str
    task: str = "transcribe"  # 'transcribe' or 'command'
    audio_s: float = 0.0
    app: str = ""
    ts: str = ""

    def __post_init__(self):
        if not self.ts:
            self.ts = datetime.datetime.now().isoformat()


def _get_history_path(storage_dir: str | Path | None = None) -> Path:
    from kural.engine.utils import get_user_app_data_path

    base = Path(storage_dir) if storage_dir else Path(get_user_app_data_path())
    return base / HISTORY_FILE


_file_lock = threading.Lock()


def append_history(entry: HistoryEntry, storage_dir: str | Path | None = None) -> bool:
    """Append a HistoryEntry to history.jsonl on disk."""
    path = _get_history_path(storage_dir)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(asdict(entry), ensure_ascii=False) + "\n"
        with _file_lock, open(path, "a", encoding="utf-8") as f:
            f.write(line)
        return True
    except Exception as e:
        logger.warning(f"Failed to append history to {path}: {e}")
        return False


def load_history(storage_dir: str | Path | None = None) -> list[dict]:
    """Load all valid history entries, oldest first."""
    path = _get_history_path(storage_dir)
    if not path.exists():
        return []

    entries = []
    with _file_lock, open(path, encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            if not line_str:
                continue
            with contextlib.suppress(json.JSONDecodeError):
                entries.append(json.loads(line_str))
    return entries


def tokenize_query(text: str) -> list[str]:
    """Tokenize query string into search terms."""
    return re.findall(r"\w+", (text or "").lower())


def search_history(
    query: str = "",
    app: str | None = None,
    task: str | None = None,
    limit: int = 50,
    storage_dir: str | Path | None = None,
) -> list[dict]:
    """Search history entries using pure BM25 ranking. Empty query returns newest."""
    entries = load_history(storage_dir)
    if not entries:
        return []

    pool = [
        e
        for e in entries
        if (not app or e.get("app") == app) and (not task or e.get("task", "transcribe") == task)
    ]

    terms = tokenize_query(query)
    if not terms:
        return list(reversed(pool))[:limit]

    docs = [tokenize_query(e.get("text", "")) for e in pool]
    n = len(docs) or 1
    avg_len = (sum(len(d) for d in docs) / n) or 1.0
    doc_freq = Counter(t for d in docs for t in set(d))
    k1, b = 1.5, 0.75

    scored = []
    for idx, (entry, doc) in enumerate(zip(pool, docs, strict=True)):
        tf = Counter(doc)
        score = 0.0
        for t in terms:
            if not tf[t]:
                hits = sum(count for word, count in tf.items() if word.startswith(t))
                if not hits:
                    continue
                freq, weight = hits, 0.5
            else:
                freq, weight = tf[t], 1.0

            idf = math.log(1 + (n - doc_freq[t] + 0.5) / (doc_freq[t] + 0.5))
            score += weight * idf * freq * (k1 + 1) / (freq + k1 * (1 - b + b * len(doc) / avg_len))

        if score > 0:
            scored.append((score, idx, entry))

    scored.sort(key=lambda s: (-s[0], -s[1]))
    return [e for _, _, e in scored[:limit]]


def _parse_entry_date(entry: dict) -> datetime.date | None:
    try:
        ts = entry.get("ts", "")
        return datetime.datetime.fromisoformat(ts).date()
    except Exception:
        return None


def compute_stats(
    today: datetime.date | None = None,
    typing_wpm: int = DEFAULT_TYPING_WPM,
    storage_dir: str | Path | None = None,
) -> dict:
    """Calculate productivity and usage statistics across all history."""
    today = today or datetime.date.today()
    entries = load_history(storage_dir)

    dictations = [e for e in entries if e.get("task", "transcribe") == "transcribe"]
    commands_count = sum(1 for e in entries if e.get("task") == "command")

    words_list = [len(str(e.get("text", "")).split()) for e in dictations]
    total_words = sum(words_list)
    total_audio_s = sum(float(e.get("audio_s", 0) or 0) for e in dictations)

    wpm = total_words / (total_audio_s / 60) if total_audio_s > 0 else 0.0
    typed_min = total_words / typing_wpm if typing_wpm else 0.0
    saved_min = max(0.0, typed_min - (total_audio_s / 60))

    # Daily streak
    days = {_parse_entry_date(e) for e in entries if _parse_entry_date(e)}
    streak, cur_d = 0, today
    if cur_d not in days:
        cur_d -= datetime.timedelta(days=1)
    while cur_d in days:
        streak += 1
        cur_d -= datetime.timedelta(days=1)

    top_apps = Counter(e.get("app") for e in entries if e.get("app")).most_common(5)

    return {
        "dictations": len(dictations),
        "commands": commands_count,
        "total_words": total_words,
        "audio_seconds": round(total_audio_s, 1),
        "wpm": round(wpm),
        "minutes_saved": round(saved_min, 1),
        "streak_days": streak,
        "top_apps": top_apps,
    }
