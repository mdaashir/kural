# MIT License — Copyright (c) 2025 Rohit Burani & Mohamed Aashir S
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/editing.py
"""Wispr Flow style smart voice text rewriting, replacements, and transformations.

Provides:
1. In-place word & phrase replacements: "replace Monday with Tuesday", "swap X for Y".
2. Code case conversions: camelCase, snake_case, kebab-case, PascalCase, CONSTANT_CASE.
3. Wrappers & blocks: quotes (“...”), parentheses, inline code (`...`), code blocks (```...```).
4. Structural line edits: alphabetical sorting, line joining, deleting last sentence.
5. Fast list & casing transforms: bullet lists, numbered lists, title case.
6. Local air-gapped LLM fallback for free-form semantic rewrites.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Fast Deterministic Transforms
# -----------------------------------------------------------------------------


def transform_bullet_list(text: str) -> str:
    """Transform text lines or sentences into a bulleted list."""
    if not text:
        return text

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) > 1:
        return "\n".join(f"• {line.lstrip('•-* ')}" for line in lines)

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) > 1:
        return "\n".join(f"• {s}" for s in sentences)

    return f"• {text}"


def transform_numbered_list(text: str) -> str:
    """Transform text lines or sentences into a numbered list."""
    if not text:
        return text

    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) > 1:
        return "\n".join(
            f"{i + 1}. {line.lstrip('0123456789.•-* ')}" for i, line in enumerate(lines)
        )

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if len(sentences) > 1:
        return "\n".join(f"{i + 1}. {sent}" for i, sent in enumerate(sentences))

    return f"1. {text}"


def transform_title_case(text: str) -> str:
    """Capitalize the first letter of each significant word."""
    if not text:
        return text
    return text.title()


def transform_uppercase(text: str) -> str:
    return (text or "").upper()


def transform_lowercase(text: str) -> str:
    return (text or "").lower()


# -----------------------------------------------------------------------------
# Code Case Conversions (Developer Voice Controls)
# -----------------------------------------------------------------------------


def _split_words(text: str) -> list[str]:
    """Split string into individual words across spaces, dashes, underscores, or camelCase."""
    # Split camelCase
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", text)
    # Split non-alphanumeric
    words = re.findall(r"[A-Za-z0-9]+", s)
    return [w.lower() for w in words if w]


def transform_camel_case(text: str) -> str:
    words = _split_words(text)
    if not words:
        return text
    return words[0] + "".join(w.capitalize() for w in words[1:])


def transform_pascal_case(text: str) -> str:
    words = _split_words(text)
    return "".join(w.capitalize() for w in words)


def transform_snake_case(text: str) -> str:
    words = _split_words(text)
    return "_".join(words)


def transform_kebab_case(text: str) -> str:
    words = _split_words(text)
    return "-".join(words)


def transform_constant_case(text: str) -> str:
    words = _split_words(text)
    return "_".join(w.upper() for w in words)


# -----------------------------------------------------------------------------
# Wrappers, Enclosures, & Structural Edits
# -----------------------------------------------------------------------------


def transform_quotes(text: str) -> str:
    return f'"{text.strip()}"'


def transform_parentheses(text: str) -> str:
    return f"({text.strip()})"


def transform_backticks(text: str) -> str:
    return f"`{text.strip()}`"


def transform_code_block(text: str) -> str:
    return f"```\n{text.strip()}\n```"


def transform_sort_lines(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if len(lines) <= 1:
        return text
    return "\n".join(sorted(lines, key=str.lower))


def transform_join_paragraph(text: str) -> str:
    return re.sub(r"\s*\n\s*", " ", text).strip()


def transform_delete_last_sentence(text: str) -> str:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    if len(parts) > 1:
        return " ".join(parts[:-1])
    return ""


# -----------------------------------------------------------------------------
# Spoken Word & Phrase Replacements ("replace X with Y")
# -----------------------------------------------------------------------------

REPLACE_PATTERN = re.compile(
    r"^(?:please\s+)?(?:replace|change|swap)\s+(?:the\s+word\s+|the\s+phrase\s+)?[\"']?(.+?)[\"']?"
    r"\s+(?:with|to|for|into)\s+[\"']?(.+?)[\"']?[.!]?$",
    re.IGNORECASE,
)

DELETE_PHRASE_PATTERN = re.compile(
    r"^(?:please\s+)?(?:delete|remove|drop)\s+(?:the\s+word\s+|the\s+phrase\s+)?[\"']?(.+?)[\"']?[.!]?$",
    re.IGNORECASE,
)


def apply_voice_replacement(instruction: str, text: str) -> tuple[str | None, str | None]:
    """Inspect instruction for targeted replacements or deletions.

    Returns (new_text, description) if matched, otherwise (None, None).
    """
    ins = (instruction or "").strip().strip(".!").strip()
    if not ins or not text:
        return None, None

    # Replace "old" with "new"
    m_rep = REPLACE_PATTERN.match(ins)
    if m_rep:
        old_val = m_rep.group(1).strip()
        new_val = m_rep.group(2).strip()
        pat = re.compile(rf"\b{re.escape(old_val)}\b", re.IGNORECASE)
        if pat.search(text):
            return pat.sub(new_val, text), f"replaced '{old_val}'"

    # Delete word/phrase
    m_del = DELETE_PHRASE_PATTERN.match(ins)
    if m_del:
        target = m_del.group(1).strip()
        if target.lower() not in ("last sentence", "lines", "bullets"):
            pat = re.compile(rf"\s*\b{re.escape(target)}\b", re.IGNORECASE)
            if pat.search(text):
                cleaned = pat.sub("", text).strip()
                cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
                return cleaned, f"removed '{target}'"

    return None, None


# Map keyword patterns to deterministic functions
FAST_TRANSFORMS = {
    # Lists
    "bullet": transform_bullet_list,
    "bullet_list": transform_bullet_list,
    "bullets": transform_bullet_list,
    "numbered": transform_numbered_list,
    "numbered_list": transform_numbered_list,
    # Casings
    "title_case": transform_title_case,
    "title": transform_title_case,
    "uppercase": transform_uppercase,
    "upper": transform_uppercase,
    "all caps": transform_uppercase,
    "lowercase": transform_lowercase,
    "lower": transform_lowercase,
    "camelcase": transform_camel_case,
    "camel case": transform_camel_case,
    "pascalcase": transform_pascal_case,
    "pascal case": transform_pascal_case,
    "snakecase": transform_snake_case,
    "snake case": transform_snake_case,
    "kebabcase": transform_kebab_case,
    "kebab case": transform_kebab_case,
    "constant case": transform_constant_case,
    # Wrappers
    "quote": transform_quotes,
    "quotes": transform_quotes,
    "double quotes": transform_quotes,
    "parentheses": transform_parentheses,
    "brackets": transform_parentheses,
    "backtick": transform_backticks,
    "backticks": transform_backticks,
    "code block": transform_code_block,
    # Structural
    "sort": transform_sort_lines,
    "sort lines": transform_sort_lines,
    "alphabetize": transform_sort_lines,
    "join lines": transform_join_paragraph,
    "single paragraph": transform_join_paragraph,
    "one paragraph": transform_join_paragraph,
    "delete last sentence": transform_delete_last_sentence,
    "remove last sentence": transform_delete_last_sentence,
}


def apply_smart_transform(
    text: str,
    instruction: str,
    llm_fallback: Any = None,
) -> str:
    """Transform text using fast deterministic transforms, replacements, or local LLM instruction."""
    clean_text = (text or "").strip()
    if not clean_text:
        return ""

    inst_clean = (instruction or "").strip()
    inst_lower = inst_clean.lower()

    # 1. Check targeted word/phrase replacements ("replace X with Y", "delete X")
    rep_text, _ = apply_voice_replacement(inst_clean, clean_text)
    if rep_text is not None:
        return rep_text

    # 2. Check deterministic fast transforms
    for key, fn in FAST_TRANSFORMS.items():
        if key in inst_lower:
            return fn(clean_text)

    # 3. Check local LLM rewrite fallback
    if llm_fallback and llm_fallback.is_available():
        prompt = (
            f"You are a professional text editing assistant. Follow this instruction precisely:\n"
            f"Instruction: {instruction}\n\n"
            f"Original Text:\n{clean_text}\n\n"
            f"Return ONLY the rewritten text without explanations or quotes:"
        )
        try:
            rewritten = llm_fallback.query(prompt)
            if rewritten and rewritten.strip():
                return rewritten.strip().strip('"').strip("'")
        except Exception as e:
            logger.warning(f"Local LLM smart transform failed: {e}")

    # Fallback to original text if no transform matched
    return clean_text
