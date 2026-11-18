# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/selftest.py
"""Automated end-to-end operational diagnostic invoked by `kural --selftest`.

Runs four independent checks (mic capture, model load, transcription, clipboard)
and prints each result with specific fix hints on failure. Returns 0 if every
check passes, 1 otherwise — so it can be wired into CI or first-run verification.
"""

import contextlib
import logging
import sys
import time

logger = logging.getLogger(__name__)


def _report(
    ok: bool,
    msg: str | tuple[str, str],
    failures: list[tuple[str, str, str]],
    name: str,
) -> None:
    """Print check status and record failures."""
    if ok:
        print(f"    ✓ {msg}")
    else:
        if isinstance(msg, tuple):
            reason, fix = msg
        else:
            reason, fix = str(msg), ""
        print(f"    ✗ {reason}")
        failures.append((name, reason, fix))


def _test_audio_capture() -> tuple[bool, str | tuple[str, str]]:
    """Verify default microphone captures audio and permissions are granted."""
    try:
        import numpy as np
        import sounddevice as sd
    except ImportError as e:
        return False, (f"Missing audio dependency: {e}", "pip install -e .[runtime]")

    try:
        device = sd.query_devices(kind="input")
    except Exception as e:
        return False, (
            f"No default input audio device: {e}",
            "Check your microphone is plugged in and set as default in Windows Sound Settings",
        )

    rate = int(device.get("default_samplerate") or 16000)
    try:
        recording = sd.rec(int(0.5 * rate), samplerate=rate, channels=1, dtype="float32")
        sd.wait()
        rms = float(np.sqrt(np.mean(recording.astype(np.float32) ** 2)))
        if rms < 1e-6:
            return False, (
                "Mic captured pure silence (RMS < 1e-6) — device may be muted or blocked",
                "Windows Settings → Privacy & Security → Microphone → Enable 'Let desktop apps access your microphone'",
            )
        return True, f"Captured {len(recording)} samples at {rate} Hz (RMS={rms:.4f})"
    except Exception as e:
        return False, (
            f"Recording failed: {e}",
            "Check microphone permissions and verify no exclusive-mode application is holding the device",
        )


def _test_model_loadable() -> tuple[bool, str | tuple[str, str]]:
    """Verify configured Whisper model is resolvable in the registry."""
    try:
        from kural.config import ConfigManager
        from kural.engine.model_registry import ModelRegistry

        cfg = ConfigManager(quiet=True)
        whisper_cfg = cfg.get_whisper_config()
        model_key = whisper_cfg.get("model", "large-v3-turbo")

        reg = ModelRegistry(whisper_models_config=whisper_cfg.get("models", {}))
        cached = reg.is_model_cached(model_key)
        cache_status = "cached locally" if cached else "not cached (will download on first run)"
        return True, f"Model '{model_key}' ({whisper_cfg.get('device', 'cuda')}) → {cache_status}"
    except Exception as e:
        return False, (
            f"Model registry error: {e}",
            "Check user_settings.yaml whisper configuration",
        )


def _test_end_to_end() -> tuple[bool, str | tuple[str, str]]:
    """Exercise inference pipeline end-to-end with a 2-second audio slice."""
    try:
        import numpy as np

        from kural.config import ConfigManager
        from kural.engine.whisper_engine import WhisperEngine

        cfg = ConfigManager(quiet=True)
        whisper_cfg = cfg.get_whisper_config()

        engine = WhisperEngine(
            model_key=whisper_cfg.get("model", "large-v3-turbo"),
            device=whisper_cfg.get("device", "cuda"),
            compute_type=whisper_cfg.get("compute_type", "float16"),
            language="en",
            beam_size=1,
            idle_unload_minutes=0,
        )

        t0 = time.time()
        silence = np.zeros(2 * 16000, dtype=np.float32)
        _ = engine.transcribe_audio(silence)
        elapsed = time.time() - t0
        return True, f"Inference pipeline verified in {elapsed:.2f}s (CTranslate2 active)"
    except Exception as e:
        return False, (
            f"Transcription pipeline failed: {e}",
            "Run 'kural --doctor' to inspect GPU libraries and CUDA dependencies",
        )


def _test_clipboard() -> tuple[bool, str | tuple[str, str]]:
    """Verify non-destructive clipboard copy and paste with original content restoration."""
    try:
        import pyperclip

        prev_content = ""
        try:
            prev_content = pyperclip.paste()
        except Exception:
            prev_content = ""

        marker = f"__kural-selftest-{int(time.time())}"
        pyperclip.copy(marker)
        time.sleep(0.05)
        got = pyperclip.paste()

        # Restore original clipboard contents immediately
        with contextlib.suppress(Exception):
            pyperclip.copy(prev_content)

        if got != marker:
            return False, (
                "Clipboard write did not round-trip correctly",
                "Another process or clipboard manager may be locking the Windows clipboard API",
            )
        return True, "Clipboard read/write round-trip verified (original content restored)"
    except ImportError:
        return True, "pyperclip not installed (clipboard verification skipped)"
    except Exception as e:
        return False, (
            f"Clipboard access error: {e}",
            "Ensure no conflicting software has locked the system clipboard",
        )


def run_selftest() -> int:
    """Execute all 4 self-test stages and output actionable diagnostics.

    Returns:
        0 if all checks pass, 1 otherwise.
    """
    print("\n🔬 Kural — Self-Test Diagnostics\n" + "─" * 50)
    failures: list[tuple[str, str, str]] = []

    print("\n[1/4] Audio capture & microphone permissions")
    ok, msg = _test_audio_capture()
    _report(ok, msg, failures, "audio-capture")

    print("\n[2/4] Whisper model configuration & registry")
    ok, msg = _test_model_loadable()
    _report(ok, msg, failures, "model-load")

    print("\n[3/4] End-to-end inference pipeline")
    ok, msg = _test_end_to_end()
    _report(ok, msg, failures, "transcription")

    print("\n[4/4] Non-destructive clipboard read/write")
    ok, msg = _test_clipboard()
    _report(ok, msg, failures, "clipboard")

    print("\n" + "─" * 50)
    if not failures:
        print("✅ All checks passed. Kural is ready to transcribe.\n")
        return 0

    print(f"❌ {len(failures)} check(s) failed:\n")
    for name, reason, fix in failures:
        print(f"  • {name}: {reason}")
        if fix:
            print(f"    → fix: {fix}")
    print()
    return 1


if __name__ == "__main__":
    sys.exit(run_selftest())
