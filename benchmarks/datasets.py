"""Dataset loader and manifest manager for ASR benchmark test sets."""

import json
import wave
from dataclasses import dataclass
from pathlib import Path

import numpy as np


@dataclass
class BenchmarkSample:
    """A test sample with audio path and ground-truth transcript."""

    sample_id: str
    audio_path: Path
    reference_text: str
    language: str
    duration_sec: float


# Default curated benchmark test items (English, Tamil, and Tanglish)
DEFAULT_TEST_ITEMS = [
    {
        "id": "en_voice_typing_1",
        "language": "en",
        "reference": "Whisper is a general purpose speech recognition model.",
    },
    {
        "id": "en_command_1",
        "language": "en",
        "reference": "Open Google Chrome and search for local speech recognition.",
    },
    {
        "id": "ta_greeting_1",
        "language": "ta",
        "reference": "வணக்கம் இது குரல் குரல்வழி தட்டச்சு சோதனை.",
    },
    {
        "id": "ta_tanglish_1",
        "language": "ta",
        "reference": "நான் குரோம் ஓபன் பண்ணி யூடியூப் பார்க்கிறேன்.",
    },
    {
        "id": "ta_command_open_1",
        "language": "ta",
        "reference": "நோட்பேடு ஓபன் பண்ணு.",
    },
    {
        "id": "ta_command_volume_1",
        "language": "ta",
        "reference": "சத்தத்தை ஏற்று.",
    },
]


def get_audio_duration(wav_path: Path | str) -> float:
    """Read the duration in seconds of a WAV file."""
    with wave.open(str(wav_path), "rb") as wf:
        frames = wf.getnframes()
        rate = wf.getframerate()
        return frames / float(rate)


def create_synthetic_wav(
    output_path: Path | str,
    duration_sec: float = 2.5,
    sample_rate: int = 16000,
    frequency: float = 440.0,
) -> Path:
    """Create a valid 16 kHz mono WAV file (used for offline tests and smoke runs)."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
    # Modulated audio signal with gentle fade-in and fade-out
    envelope = np.sin(np.pi * t / duration_sec) ** 2
    samples = (0.5 * np.sin(2 * np.pi * frequency * t) * envelope).astype(np.float32)

    int_samples = (samples * 32767).astype(np.int16)

    with wave.open(str(output_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())

    return output_path


def load_or_create_samples(samples_dir: Path | str | None = None) -> list[BenchmarkSample]:
    """Load benchmark samples from samples_dir, creating standard test clips if absent."""
    samples_dir = Path(__file__).parent / "samples" if samples_dir is None else Path(samples_dir)

    samples_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = samples_dir / "manifest.json"

    samples: list[BenchmarkSample] = []

    if manifest_path.exists():
        with open(manifest_path, encoding="utf-8") as f:
            data = json.load(f)
            for item in data.get("samples", []):
                wav_path = samples_dir / item["file"]
                if wav_path.exists():
                    duration = get_audio_duration(wav_path)
                    samples.append(
                        BenchmarkSample(
                            sample_id=item["id"],
                            audio_path=wav_path,
                            reference_text=item["reference"],
                            language=item["language"],
                            duration_sec=duration,
                        )
                    )
        if samples:
            return samples

    # Populate default samples directory
    manifest_data = {"samples": []}
    for item in DEFAULT_TEST_ITEMS:
        wav_file = f"{item['id']}.wav"
        wav_path = samples_dir / wav_file
        if not wav_path.exists():
            create_synthetic_wav(wav_path, duration_sec=3.0)
        duration = get_audio_duration(wav_path)
        sample = BenchmarkSample(
            sample_id=item["id"],
            audio_path=wav_path,
            reference_text=item["reference"],
            language=item["language"],
            duration_sec=duration,
        )
        samples.append(sample)
        manifest_data["samples"].append(
            {
                "id": item["id"],
                "file": wav_file,
                "reference": item["reference"],
                "language": item["language"],
            }
        )

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, ensure_ascii=False, indent=2)

    return samples
