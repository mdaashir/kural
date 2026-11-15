# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/app_rules.py
"""Per-application formatting styles and delivery rules.

Matches the active foreground window against layered app rules to customize formatting
(e.g., verbatim in code editors and terminals, formal in email, casual in chat) or suppress
delivery completely for password managers.
"""

import logging
import re
from dataclasses import dataclass
from pathlib import Path

from kural.config.defaults_merge import load_layered
from kural.engine.utils import get_user_app_data_path

logger = logging.getLogger(__name__)

USER_RULES_FILE = "app_rules.yaml"
DEFAULTS_RULES_FILE = "app_rules.defaults.yaml"

USER_FILE_HEADER = """\
# Kural — Custom Per-Application Rules
#
# Rules configured here override or extend the shipped package rules.
# You can override a shipped rule by matching its id, or define new rules.
#
"""


@dataclass
class FormattingStyle:
    """Settings controlling capitalization and punctuation styles."""

    name: str = "default"
    capitalize_first: bool = True
    ensure_punctuation: bool = True
    strip_trailing_period: bool = False
    lowercase: bool = False


# Pre-defined styles
STYLES = {
    "formal": FormattingStyle(
        name="formal",
        capitalize_first=True,
        ensure_punctuation=True,
        strip_trailing_period=False,
        lowercase=False,
    ),
    "casual": FormattingStyle(
        name="casual",
        capitalize_first=False,
        ensure_punctuation=False,
        strip_trailing_period=True,
        lowercase=False,
    ),
    "verbatim": FormattingStyle(
        name="verbatim",
        capitalize_first=False,
        ensure_punctuation=False,
        strip_trailing_period=True,
        lowercase=False,
    ),
}


def apply_formatting_style(text: str, style_name: str = "formal") -> str:
    """Format transcribed text according to the selected style."""
    if not text:
        return ""

    style = STYLES.get(style_name.lower(), STYLES["formal"])
    t = text.strip()

    if style.lowercase:
        t = t.lower()
    elif style.capitalize_first and t and not t[0].isupper():
        t = t[0].upper() + t[1:]

    if style.strip_trailing_period and t.endswith("."):
        t = t.rstrip(".")

    if style.ensure_punctuation and t and not re.search(r"[.!?]$", t):
        t += "."

    return t


class AppRules:
    """Evaluates the foreground application against configured rules."""

    def __init__(self, user_rules_path: Path | str | None = None):
        if user_rules_path is None:
            self._path = Path(get_user_app_data_path()) / USER_RULES_FILE
        else:
            self._path = Path(user_rules_path)

        self.rules: list[dict] = []
        self._mtime = 0.0
        self._reload_from_disk()

    def _reload_from_disk(self) -> None:
        try:
            merged, _ = load_layered(
                defaults_filename=DEFAULTS_RULES_FILE,
                user_path=self._path,
                section="rules",
                header=USER_FILE_HEADER,
                id_key="id",
            )
            self.rules = [r for r in merged if isinstance(r, dict)]
            self._mtime = self._path.stat().st_mtime if self._path.exists() else 0.0
        except Exception as e:
            logger.warning(f"Could not load app rules: {e}")
            self.rules = []

    def _reload_if_changed(self) -> None:
        try:
            if self._path.exists():
                mtime = self._path.stat().st_mtime
                if mtime > self._mtime:
                    logger.info("Reloading app_rules.yaml due to file change")
                    self._reload_from_disk()
        except OSError:
            pass

    def match_rule(self, exe: str, title: str) -> dict | None:
        """Find the first matching rule for an executable name and/or window title."""
        self._reload_if_changed()

        e_clean = (exe or "").strip().lower()
        t_clean = (title or "").strip().lower()

        for rule in self.rules:
            if rule.get("disabled", False):
                continue

            patterns = rule.get("match") or []
            if isinstance(patterns, str):
                patterns = [patterns]

            for p in patterns:
                p_str = str(p).strip().lower()
                if p_str and (p_str in e_clean or p_str in t_clean):
                    return rule

        return None
