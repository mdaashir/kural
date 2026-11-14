"""Conftest for engine tests: inject fake heavy dependencies before any module is imported."""

import sys
import types
from unittest.mock import MagicMock


def _inject_fake_deps() -> None:
    """Put stub modules into sys.modules so engine files can be imported without real deps."""
    # faster_whisper
    if "faster_whisper" not in sys.modules:
        fake_fw = types.ModuleType("faster_whisper")
        fake_fw.WhisperModel = MagicMock
        sys.modules["faster_whisper"] = fake_fw
    else:
        fw = sys.modules["faster_whisper"]
        if not hasattr(fw, "WhisperModel"):
            fw.WhisperModel = MagicMock

    # faster_whisper.utils with _MODELS
    if "faster_whisper.utils" not in sys.modules:
        fake_utils = types.ModuleType("faster_whisper.utils")
        fake_utils._MODELS = {
            "base": "Systran/faster-whisper-base",
            "large-v3-turbo": "Systran/faster-whisper-large-v3-turbo",
        }
        sys.modules["faster_whisper.utils"] = fake_utils
        sys.modules["faster_whisper"].utils = fake_utils  # type: ignore[attr-defined]

    # ctranslate2
    if "ctranslate2" not in sys.modules:
        sys.modules["ctranslate2"] = types.ModuleType("ctranslate2")


_inject_fake_deps()
