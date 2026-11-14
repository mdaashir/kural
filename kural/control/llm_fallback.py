# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported from ROHITCRAFTSYT/WhispLocal/whisp/locallm.py
"""Optional local-LLM intent fallback for unfamiliar command phrasing.

When fast exact and regex pattern matching fails on an unusual phrase, an optional
local model (GGUF via llama-cpp-python or ONNX) maps the phrasing to a canonical command.
Crucially, the LLM never executes anything directly: its reply is strictly sanitized and
must parse through the deterministic intent parser before execution.
"""

import logging
import os
import re
import threading

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SEC = 6.0

_SYSTEM_PROMPT = (
    "You map a spoken computer instruction to ONE canonical command from this fixed list:\n"
    "- open <app>, close <app>, switch to <app>\n"
    "- volume up, volume down, set volume to <0-100>, mute\n"
    "- minimize window, maximize window, snap left, snap right, show desktop\n"
    "- play, pause, next song, previous song\n"
    "- shut down the computer, restart the computer, cancel shutdown\n"
    "- search for <query>, search <query> in youtube\n\n"
    "Reply with ONLY the canonical command, nothing else. If the instruction is not a "
    "computer command, reply exactly NONE.\n"
)


def build_prompt(phrase: str) -> str:
    """Construct the few-shot prompt shown to the local model."""
    return f"{_SYSTEM_PROMPT}\nInstruction: {phrase.strip()}\nCommand:"


def sanitize_llm_output(text: str) -> str | None:
    """Sanitize the model's raw text response into a canonical command phrase."""
    t = (text or "").strip()
    if not t:
        return None

    # Strip markdown backticks and surrounding quotes
    t = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", t)
    t = t.strip("`\"' ")
    t = re.sub(r"\s+", " ", t).strip()

    # If model answers "Command: open chrome", strip prefix
    m = re.match(r"^(?:command|canonical command|reply)\s*[:\-]\s*(.+)$", t, re.IGNORECASE)
    if m:
        t = m.group(1).strip()

    if not t or t.upper() == "NONE":
        return None

    # Remove trailing punctuation that might break parser
    t = t.rstrip(".!?,")
    return t.strip() or None


class LocalLLMFallback:
    """Wrapper around a local language model for resolving unrecognized commands."""

    def __init__(
        self,
        model_path: str = "",
        timeout_sec: float = DEFAULT_TIMEOUT_SEC,
        enabled: bool = False,
    ):
        self.model_path = (model_path or "").strip()
        self.timeout_sec = timeout_sec
        self.enabled = enabled and bool(self.model_path)
        self._lock = threading.RLock()
        self._session = None

    def is_available(self) -> bool:
        """True if fallback is enabled and points to an existing model path."""
        return self.enabled and os.path.exists(self.model_path)

    def resolve_command(self, phrase: str) -> str | None:
        """Query the local model on a background thread with a timeout.

        Returns a sanitized canonical command string, or None if timed out,
        failed, or rejected as NONE.
        """
        if not self.is_available():
            return None

        result_box: list[str | None] = [None]

        def _infer():
            try:
                raw_reply = self._generate_text(phrase)
                result_box[0] = sanitize_llm_output(raw_reply)
            except Exception as e:
                logger.warning(f"Local LLM inference failed: {e}")

        thread = threading.Thread(target=_infer, daemon=True, name="local-llm-fallback")
        thread.start()
        thread.join(timeout=self.timeout_sec)

        if thread.is_alive():
            logger.warning(f"Local LLM fallback timed out after {self.timeout_sec}s for '{phrase}'")
            return None

        return result_box[0]

    def _generate_text(self, phrase: str) -> str:
        """Generate text from the local model backend (llama-cpp or onnx)."""
        prompt = build_prompt(phrase)

        with self._lock:
            # 1. Plain mock / custom callable for testing
            if callable(self._session):
                return self._session(prompt)

            # 2. GGUF via llama-cpp-python
            if self.model_path.lower().endswith(".gguf"):
                import llama_cpp

                if self._session is None:
                    logger.info(f"Loading local GGUF model: {self.model_path}")
                    self._session = llama_cpp.Llama(
                        model_path=self.model_path,
                        n_ctx=512,
                        verbose=False,
                    )
                out = self._session(
                    prompt,
                    max_tokens=32,
                    stop=["\n", "Instruction:"],
                    temperature=0.1,
                )
                return out["choices"][0]["text"]

            return ""
