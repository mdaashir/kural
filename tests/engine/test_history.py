"""Tests for kural.engine.history — JSONL logging, BM25 ranking, and stats calculation."""

import datetime

from kural.engine.history import (
    HistoryEntry,
    append_history,
    compute_stats,
    load_history,
    search_history,
    tokenize_query,
)


class TestHistoryStorage:
    def test_append_and_load_history(self, tmp_path):
        assert load_history(tmp_path) == []

        e1 = HistoryEntry(
            text="First spoken dictation", task="transcribe", audio_s=2.5, app="code.exe"
        )
        e2 = HistoryEntry(text="open notepad", task="command", audio_s=1.0)

        assert append_history(e1, storage_dir=tmp_path) is True
        assert append_history(e2, storage_dir=tmp_path) is True

        loaded = load_history(tmp_path)
        assert len(loaded) == 2
        assert loaded[0]["text"] == "First spoken dictation"
        assert loaded[0]["app"] == "code.exe"
        assert loaded[1]["task"] == "command"


class TestBM25Search:
    def setup_method(self):
        self.entries = [
            {
                "text": "Python machine learning pipeline with PyTorch",
                "task": "transcribe",
                "app": "code.exe",
            },
            {
                "text": "Daily standup meeting notes and action items",
                "task": "transcribe",
                "app": "slack.exe",
            },
            {
                "text": "Python web scraper using beautifulsoup",
                "task": "transcribe",
                "app": "code.exe",
            },
            {"text": "open chrome", "task": "command"},
        ]

    def test_tokenize_query(self):
        assert tokenize_query("Hello, World! 123") == ["hello", "world", "123"]
        assert tokenize_query("") == []

    def test_bm25_search_ranks_relevant_first(self, tmp_path):
        for e in self.entries:
            append_history(
                HistoryEntry(
                    text=e["text"], task=e.get("task", "transcribe"), app=e.get("app", "")
                ),
                storage_dir=tmp_path,
            )

        results = search_history("machine learning", storage_dir=tmp_path)
        assert len(results) >= 1
        assert "machine learning" in results[0]["text"]

    def test_empty_query_returns_newest(self, tmp_path):
        for e in self.entries:
            append_history(
                HistoryEntry(text=e["text"], task=e.get("task", "transcribe")),
                storage_dir=tmp_path,
            )
        newest = search_history("", limit=2, storage_dir=tmp_path)
        assert len(newest) == 2
        assert newest[0]["text"] == "open chrome"


class TestStatsComputation:
    def test_compute_stats_metrics(self, tmp_path):
        today = datetime.date(2026, 11, 15)
        # Add 2 dictations of 10 words each over 6 seconds total
        append_history(
            HistoryEntry(
                text="one two three four five six seven eight nine ten",
                task="transcribe",
                audio_s=3.0,
                app="code.exe",
                ts="2026-11-15T10:00:00",
            ),
            storage_dir=tmp_path,
        )
        append_history(
            HistoryEntry(
                text="eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty",
                task="transcribe",
                audio_s=3.0,
                app="code.exe",
                ts="2026-11-15T10:05:00",
            ),
            storage_dir=tmp_path,
        )
        append_history(
            HistoryEntry(
                text="volume up",
                task="command",
                audio_s=1.0,
                ts="2026-11-15T10:10:00",
            ),
            storage_dir=tmp_path,
        )

        stats = compute_stats(today=today, typing_wpm=40, storage_dir=tmp_path)
        assert stats["dictations"] == 2
        assert stats["commands"] == 1
        assert stats["total_words"] == 20
        assert stats["audio_seconds"] == 6.0
        # 20 words in 6 seconds = 200 WPM
        assert stats["wpm"] == 200
        # Time saved > 0 vs 40 WPM manual typing
        assert stats["minutes_saved"] > 0
        assert stats["streak_days"] == 1
        assert stats["top_apps"][0] == ("code.exe", 2)
