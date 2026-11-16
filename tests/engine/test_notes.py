"""Tests for kural.engine.notes — voice notes and Obsidian vault quick-capture."""

from pathlib import Path

from kural.engine.notes import (
    _is_within_folder,
    get_default_notes_dir,
    save_voice_note,
)


class TestVoiceNotes:
    def test_default_notes_dir(self):
        d = get_default_notes_dir()
        assert isinstance(d, Path)
        assert "Kural Notes" in str(d)

    def test_save_empty_note_returns_false(self):
        ok, msg = save_voice_note("")
        assert ok is False
        assert "Nothing to note" in msg

    def test_save_note_creates_file_with_frontmatter(self, tmp_path):
        ok, msg = save_voice_note("Discuss architecture roadmap with team", vault_dir=tmp_path)
        assert ok is True
        assert "Saved to today's note" in msg

        files = list(tmp_path.glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "tags: [kural, voice-note]" in content
        assert "Discuss architecture roadmap with team." in content

    def test_save_multiple_notes_appends(self, tmp_path):
        save_voice_note("First thought", vault_dir=tmp_path)
        save_voice_note("Second thought", vault_dir=tmp_path)

        files = list(tmp_path.glob("*.md"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "First thought." in content
        assert "Second thought." in content

    def test_sandboxing_path_traversal_prevention(self, tmp_path):
        # Path escaping the base folder
        escaped_file = tmp_path.parent / "escape.md"
        assert _is_within_folder(tmp_path, escaped_file) is False
