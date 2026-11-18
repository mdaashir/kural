# MIT License — Copyright (c) 2025 Rohit Burani / ROHITCRAFTSYT
# Ported and adapted from ROHITCRAFTSYT/WhispLocal/whisp/cues.py
"""Soft synthesized audio cues for voice typing (Wispr Flow style).

Generates gentle musical chime sequences with smooth attack and exponential decay,
synthesized directly into in-memory WAV byte arrays. Completely eliminates harsh
square-wave beeps and requires zero external audio asset files on disk.
Pure standard library (wave, struct, math).
"""

import io
import logging
import math
import struct
import threading
import wave

logger = logging.getLogger(__name__)

SAMPLE_RATE = 22050

# Note definitions: list of (frequency_hz, duration_seconds, gain_amplitude)
CUE_NOTES = {
    # Rising two-tone chime indicating listening has started (E5 -> B5)
    "start": [(659.25, 0.07, 0.35), (987.77, 0.11, 0.35)],
    # Falling two-tone chime confirming recording stopped / transcribing (B5 -> E5)
    "stop": [(987.77, 0.07, 0.30), (659.25, 0.10, 0.30)],
    # Bright confirmation chord on successful text delivery (G5 -> C6)
    "done": [(783.99, 0.06, 0.25), (1046.50, 0.12, 0.25)],
    # Warm low double-tone on blocked action or error (A3 -> F3)
    "error": [(220.00, 0.12, 0.40), (174.61, 0.18, 0.40)],
    # Harmonic triple chime for voice transforms and text rewrites (C5 -> E5 -> G5)
    "transform": [
        (523.25, 0.06, 0.30),
        (659.25, 0.06, 0.30),
        (783.99, 0.10, 0.30),
    ],
}

_cue_cache: dict[str, bytes] = {}
_cache_lock = threading.Lock()


def synth_cue_wav(notes: list[tuple[float, float, float]], rate: int = SAMPLE_RATE) -> bytes:
    """Render a sequence of musical chime notes to an in-memory 16-bit mono WAV buffer."""
    samples = []
    for freq, dur, gain in notes:
        n_samples = int(rate * dur)
        attack_samples = max(1, int(rate * 0.006))  # 6ms smooth attack
        for i in range(n_samples):
            # Smooth attack envelope combined with exponential decay
            env = min(1.0, i / attack_samples) * math.exp(-4.0 * i / n_samples)
            # Add a quiet octave partial (harmonic) for a softer, bell-like body
            val = (
                math.sin(2.0 * math.pi * freq * i / rate)
                + 0.25 * math.sin(4.0 * math.pi * freq * i / rate)
            ) / 1.25
            sample_val = int(max(-1.0, min(1.0, val * env * gain)) * 32767.0)
            samples.append(sample_val)

        # 12ms silent gap between notes in sequence
        samples.extend([0] * int(rate * 0.012))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    return buf.getvalue()


def get_cue_wav_bytes(cue_name: str) -> bytes:
    """Retrieve pre-synthesized WAV byte array for named cue from memory cache."""
    with _cache_lock:
        if cue_name not in _cue_cache:
            notes = CUE_NOTES.get(cue_name, CUE_NOTES["done"])
            _cue_cache[cue_name] = synth_cue_wav(notes)
        return _cue_cache[cue_name]
