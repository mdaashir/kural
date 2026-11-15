# MIT License — Copyright (c) 2025 Rohit Burani & Mohamed Aashir S
"""Wispr Flow style smart voice text rewriting and transformations.

Provides deterministic fast text transforms (bullet lists, title casing, etc.)
and AI-assisted inline rewrites using Kural's air-gapped local LLM.
"""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def transform_bullet_list(text: str) -> str:
    """Transform text lines or sentences into a bulleted list."""
    if not text:
        return text

    # If already multi-line, prefix each non-empty line with a bullet
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if len(lines) > 1:
        return "\n".join(f"• {line.lstrip('•-* ')}" for line in lines)

    # Otherwise split on sentence boundaries
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


FAST_TRANSFORMS = {
    "bullet": transform_bullet_list,
    "bullet_list": transform_bullet_list,
    "bullets": transform_bullet_list,
    "numbered": transform_numbered_list,
    "numbered_list": transform_numbered_list,
    "title_case": transform_title_case,
    "title": transform_title_case,
    "uppercase": transform_uppercase,
    "upper": transform_uppercase,
    "lowercase": transform_lowercase,
    "lower": transform_lowercase,
}


def apply_smart_transform(
    text: str,
    instruction: str,
    llm_fallback: Any = None,
) -> str:
    """Transform text using fast deterministic transforms or local LLM instruction.

    Args:
        text: The selected text or last dictation to rewrite.
        instruction: Spoken transformation command (e.g., 'bullet that', 'make formal',
                     'translate to Tamil', 'summarize').
        llm_fallback: Optional LocalLLMFallback instance for natural language rewrites.
    """
    clean_text = (text or "").strip()
    if not clean_text:
        return ""

    inst_lower = (instruction or "").lower().strip()

    # 1. Check deterministic fast transforms
    for key, fn in FAST_TRANSFORMS.items():
        if key in inst_lower:
            return fn(clean_text)

    # 2. Check local LLM rewrite fallback
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
