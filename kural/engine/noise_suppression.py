# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/noise_suppression.py
"""Optional spectral-gating noise reduction applied to audio before Whisper inference.

Wraps the optional `noisereduce` library (spectral subtraction). Disabled by default;
enable via `audio.noise_suppression.enabled: true` in config or via the Settings UI.
Falls back to clean passthrough silently when the library is not installed or on any
processing error. Never raises exceptions.
"""

import logging

import numpy as np

logger = logging.getLogger(__name__)


def apply_noise_reduction(
    audio: np.ndarray,
    sample_rate: int = 16000,
    strength: float = 0.75,
) -> np.ndarray:
    """Apply spectral noise gating to reduce stationary background noise.

    Args:
        audio: 1D or 2D float32 audio waveform.
        sample_rate: Audio sampling frequency in Hz (default: 16000).
        strength: Proportion of noise reduction between 0.0 and 1.0 (default: 0.75).

    Returns:
        Noise-reduced float32 numpy array on success, or original array on failure.
    """
    if audio is None or len(audio) == 0:
        return audio

    try:
        import noisereduce as nr

        flat = audio.flatten()
        # Clamp strength between 0.0 and 1.0
        prop = max(0.0, min(1.0, float(strength)))
        reduced = nr.reduce_noise(y=flat, sr=sample_rate, prop_decrease=prop)
        return reduced.reshape(audio.shape).astype(np.float32)
    except ImportError:
        logger.debug(
            "noisereduce is not installed; skipping noise suppression (install with: pip install noisereduce)"
        )
        return audio
    except Exception as e:
        logger.warning(f"Noise reduction failed: {e}")
        return audio
