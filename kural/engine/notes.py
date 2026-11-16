# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/obsidian.py
"""Voice notes and Obsidian vault quick-capture.

Saves captured voice notes as formatted daily Markdown files with YAML frontmatter
and timestamped bullet entries. Sandboxed to prevent path traversal outside the
configured vault or notes directory. Zero network calls, 100% private.
"""

import logging
import os
import time
from pathlib import Path

logger = logging.getLogger(__name__)

DEFAULT_SUBFOLDER = "Kural Notes"


def get_default_notes_dir() -> Path:
    """Return default notes directory in user's Documents folder."""
    docs = Path(os.path.expanduser("~")) / "Documents"
    return docs / DEFAULT_SUBFOLDER


def _is_within_folder(base_folder: Path, target_path: Path) -> bool:
    """Ensure target path does not escape base directory via symlinks or traversal."""
    try:
        base_real = Path(os.path.realpath(base_folder))
        target_real = Path(os.path.realpath(target_path))
        return os.path.commonpath([str(base_real), str(target_real)]) == str(base_real)
    except Exception:
        return False


def save_voice_note(text: str, vault_dir: str | Path | None = None) -> tuple[bool, str]:
    """Append text to today's daily Markdown note in the vault.

    Returns (success, message).
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return False, "Nothing to note"

    base_dir = Path(vault_dir) if vault_dir else get_default_notes_dir()

    today_str = time.strftime("%Y-%m-%d")
    note_file = base_dir / f"{today_str}.md"

    # Sandboxing validation
    if not _is_within_folder(base_dir, note_file):
        return False, "Refusing to write outside the configured vault folder"

    try:
        base_dir.mkdir(parents=True, exist_ok=True)
        is_new = not note_file.exists()

        with open(note_file, "a", encoding="utf-8") as f:
            if is_new:
                f.write(
                    f"---\n"
                    f"created: {today_str}\n"
                    f"source: Kural\n"
                    f"tags: [kural, voice-note]\n"
                    f"---\n\n"
                    f"# Voice Notes — {today_str}\n\n"
                )

            stamp = time.strftime("%H:%M")
            body = clean_text[0].upper() + clean_text[1:] if clean_text else clean_text
            if not body.endswith((".", "!", "?")):
                body += "."

            f.write(f"- **{stamp}** {body}\n")

        logger.info(f"Voice note saved to {note_file}")
        return True, "Saved to today's note in Obsidian"
    except Exception as e:
        logger.error(f"Failed to save voice note: {e}")
        return False, f"Could not write note: {e}"
