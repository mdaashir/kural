# MIT License — Copyright (c) 2026 Kural Project
# Inspired by anomalyco/hex (https://github.com/anomalyco/hex)
"""Offline audio file transcription CLI and batch inference pipeline.

Enables offline transcription of recorded audio files (WAV, MP3, M4A, FLAC, OGG)
using local GPU-accelerated Whisper models without live microphone capture.

Supports output formatting as:
- plain text ('text')
- SubRip subtitles ('srt') with precise millisecond timestamps
- structured segment array ('json')
"""

import json
import logging
import wave
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

VALID_FORMATS = {"text", "srt", "json"}


def format_timestamp_srt(seconds: float) -> str:
    """Format seconds float into standard SRT timestamp HH:MM:SS,mmm."""
    if seconds < 0:
        seconds = 0.0
    total_millis = int(round(seconds * 1000.0))
    hours = total_millis // 3_600_000
    total_millis %= 3_600_000
    minutes = total_millis // 60_000
    total_millis %= 60_000
    secs = total_millis // 1000
    millis = total_millis % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def load_audio_file(file_path: str | Path, target_sr: int = 16000) -> np.ndarray:
    """Load an audio file into a 16 kHz mono float32 numpy array.

    Uses Python's standard library `wave` for standard WAV files, falling back to
    `soundfile` if installed for other formats (MP3, M4A, FLAC).

    Raises:
        FileNotFoundError: If the target audio file does not exist.
        ValueError: If audio data cannot be decoded into a valid waveform.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    wav_decode_error: Exception | None = None
    if path.suffix.lower() == ".wav":
        try:
            with wave.open(str(path), "rb") as wf:
                channels = wf.getnchannels()
                sample_width = wf.getsampwidth()
                framerate = wf.getframerate()
                n_frames = wf.getnframes()
                raw_bytes = wf.readframes(n_frames)

            if sample_width == 1:
                # 8-bit unsigned PCM
                samples = (
                    np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0
                ) / 128.0
            elif sample_width == 2:
                # 16-bit signed PCM
                samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
            elif sample_width == 3:
                # 24-bit signed little-endian PCM, sign-extended to int32.
                packed = np.frombuffer(raw_bytes, dtype=np.uint8).reshape(-1, 3).astype(np.int32)
                values = packed[:, 0] | (packed[:, 1] << 8) | (packed[:, 2] << 16)
                values = (values ^ 0x800000) - 0x800000
                samples = values.astype(np.float32) / 8388608.0
            elif sample_width == 4:
                # 32-bit signed int PCM (WAVE_FORMAT_PCM)
                samples = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0
            else:
                raise ValueError(f"Unsupported WAV sample width: {sample_width} bytes")

            # Convert stereo / multichannel to mono by averaging channels
            if channels > 1:
                samples = samples.reshape(-1, channels).mean(axis=1)

            # Resample to target_sr if necessary
            if framerate != target_sr and len(samples) > 0:
                duration = len(samples) / framerate
                target_length = int(duration * target_sr)
                # High-quality soxr resampling if available, else linear interpolation
                try:
                    import soxr

                    samples = soxr.resample(samples, framerate, target_sr)
                except ImportError:
                    orig_indices = np.linspace(0, len(samples) - 1, num=len(samples))
                    target_indices = np.linspace(0, len(samples) - 1, num=target_length)
                    samples = np.interp(target_indices, orig_indices, samples).astype(np.float32)

            return samples.astype(np.float32)
        except Exception as e:
            wav_decode_error = e
            logger.debug(f"Standard wave reader failed for {path.name}: {e}")

    # Try soundfile for unsupported WAV encodings and non-WAV formats (MP3, FLAC, OGG).
    try:
        import soundfile as sf

        data, sr = sf.read(str(path), dtype="float32")
        if data.ndim > 1:
            data = data.mean(axis=1)

        if sr != target_sr and len(data) > 0:
            try:
                import soxr

                data = soxr.resample(data, sr, target_sr)
            except ImportError:
                duration = len(data) / sr
                target_len = int(duration * target_sr)
                orig_idx = np.linspace(0, len(data) - 1, num=len(data))
                target_idx = np.linspace(0, len(data) - 1, num=target_len)
                data = np.interp(target_idx, orig_idx, data).astype(np.float32)

        return data.astype(np.float32)
    except ImportError:
        if wav_decode_error is not None:
            raise ValueError(
                f"Could not decode WAV file '{file_path}' with the standard wave reader "
                f"({wav_decode_error}). Install 'soundfile' to decode this WAV encoding."
            ) from wav_decode_error
    except Exception as e:
        logger.debug(f"soundfile read failed for {path.name}: {e}")
        if wav_decode_error is not None:
            raise ValueError(
                f"Could not decode WAV file '{file_path}' with the standard wave reader "
                f"({wav_decode_error}) or soundfile ({e})."
            ) from e
        raise ValueError(f"Could not decode audio file '{file_path}' with soundfile: {e}") from e

    raise ValueError(
        f"Could not decode audio file '{file_path}'. For non-WAV formats (MP3, M4A, FLAC), "
        "ensure 'soundfile' is installed."
    )


class SegmentInfo:
    """Represents a transcribed speech segment."""

    def __init__(self, start: float, end: float, text: str):
        self.start = float(start)
        self.end = float(end)
        self.text = str(text).strip()


def format_segments(segments: list[SegmentInfo], output_format: str = "text") -> str:
    """Format a list of transcribed segments into text, srt, or json."""
    fmt = output_format.lower().strip()
    if fmt not in VALID_FORMATS:
        raise ValueError(f"Invalid output format '{output_format}'; choose from {VALID_FORMATS}")

    if fmt == "text":
        return "\n".join(s.text for s in segments if s.text).strip()

    if fmt == "srt":
        srt_lines = []
        idx = 1
        for s in segments:
            if not s.text:
                continue
            t_start = format_timestamp_srt(s.start)
            t_end = format_timestamp_srt(s.end)
            srt_lines.append(f"{idx}\n{t_start} --> {t_end}\n{s.text}\n")
            idx += 1
        return "\n".join(srt_lines).strip()

    if fmt == "json":
        data = [
            {
                "id": idx + 1,
                "start": round(s.start, 3),
                "end": round(s.end, 3),
                "text": s.text,
            }
            for idx, s in enumerate(segments)
            if s.text
        ]
        return json.dumps(data, indent=2, ensure_ascii=False)

    return ""


def transcribe_file(
    file_path: str | Path,
    language: str | None = None,
    model_key: str | None = None,
    output_format: str = "text",
    output_path: str | Path | None = None,
    engine: Any | None = None,
) -> str:
    """Transcribe an audio file offline using local Whisper inference.

    Args:
        file_path: Path to the target audio file.
        language: Language code ('en', 'ta', or None for auto-detect).
        model_key: Whisper model variant (e.g. 'large-v3-turbo').
        output_format: Output format ('text', 'srt', 'json').
        output_path: Optional destination file path. If None, prints to stdout.
        engine: Optional pre-initialized WhisperEngine instance.

    Returns:
        Formatted transcription string.
    """
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file does not exist: {file_path}")

    # Load and resample audio waveform
    audio_data = load_audio_file(path)

    # Initialize Whisper engine if not provided
    if engine is None:
        from kural.config import ConfigManager
        from kural.engine.model_registry import ModelRegistry
        from kural.engine.whisper_engine import WhisperEngine

        cfg = ConfigManager(quiet=True)
        whisper_cfg = cfg.get_whisper_config()
        registry = ModelRegistry(whisper_models_config=whisper_cfg.get("models", {}))

        chosen_model = model_key or whisper_cfg.get("model", "large-v3-turbo")
        chosen_lang = language or whisper_cfg.get("language", "en")
        device = whisper_cfg.get("device", "cuda")
        compute_type = whisper_cfg.get("compute_type", "float16")
        indic_script = whisper_cfg.get("indic_script", "native")

        engine = WhisperEngine(
            model_key=chosen_model,
            device=device,
            compute_type=compute_type,
            language=chosen_lang,
            indic_script=indic_script,
            idle_unload_minutes=0,
            model_registry=registry,
        )

    # Ensure model is initialized
    if getattr(engine, "model", None) is None and hasattr(engine, "_load_model"):
        engine._load_model()

    # Transcribe audio array into segments
    segments_list: list[SegmentInfo] = []
    if getattr(engine, "model", None) is not None:
        model = engine.model
        kwargs: dict[str, Any] = {
            "beam_size": getattr(engine, "beam_size", 5),
            "task": getattr(engine, "task", "transcribe"),
        }
        lang = language or getattr(engine, "language", None)
        if lang:
            kwargs["language"] = lang

        # Add script primers for Tamil
        from kural.engine.whisper_engine import ROMAN_PRIMER_TAMIL, SCRIPT_PRIMER_TAMIL

        if lang == "ta":
            indic_mode = getattr(engine, "indic_script", "native")
            kwargs["initial_prompt"] = (
                ROMAN_PRIMER_TAMIL if indic_mode == "roman" else SCRIPT_PRIMER_TAMIL
            )

        segs_iter, _ = model.transcribe(audio_data, **kwargs)
        for seg in segs_iter:
            segments_list.append(SegmentInfo(start=seg.start, end=seg.end, text=seg.text))
    else:
        # Fallback to transcribe_audio if model is abstracted
        text = engine.transcribe_audio(audio_data) or ""
        duration = float(len(audio_data) / 16000.0)
        segments_list.append(SegmentInfo(start=0.0, end=duration, text=text))

    formatted = format_segments(segments_list, output_format=output_format)

    # Write to destination file if specified
    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(formatted, encoding="utf-8")
        print(f"✓ Transcript written to: {out_p}")
    else:
        print(formatted)

    return formatted
