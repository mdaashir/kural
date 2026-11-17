# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/audio_gain.py
"""Whisper mode adaptive gain booster for quiet or whispered speech.

Lifts quiet recordings (whispering late at night, distant microphone) to a level
Whisper transcribes reliably. Scales volume up to a capped maximum factor,
leaving normal speech untouched. Pure silence and background noise floors below
SILENCE_PEAK are never amplified, preventing speech-recognition hallucinations.
Pure numpy, zero extra dependencies.
"""

import numpy as np

# Target level the loud portions of speech are brought up to (in full-scale units).
# Kept safely below 1.0 to prevent digital clipping.
TARGET_PEAK = 0.6

# Audio peak below this threshold is treated as silence or muted mic, not quiet speech.
# Boosting below this level would amplify ambient hiss into hallucination bait.
SILENCE_PEAK = 1e-3


def boost_quiet_audio(audio: np.ndarray, max_gain: float = 8.0) -> np.ndarray:
    """Scale audio so loud portions reach TARGET_PEAK, up to max_gain.

    Uses 99.9th percentile peak estimation to reject acoustic pops or clicks.
    Never scales downward (gain <= 1.0 leaves audio untouched).
    """
    if audio is None or audio.size == 0:
        return audio

    peak = float(np.percentile(np.abs(audio), 99.9))
    if peak < SILENCE_PEAK:
        return audio

    gain = min(float(max_gain), TARGET_PEAK / peak)
    if gain <= 1.0:
        return audio

    return np.clip(audio * gain, -1.0, 1.0).astype(audio.dtype, copy=False)
