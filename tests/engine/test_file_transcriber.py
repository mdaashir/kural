"""Tests for kural.engine.file_transcriber — offline audio file transcription CLI."""

import json
import sys
import wave
from unittest.mock import MagicMock

import numpy as np
import pytest

from kural.engine.file_transcriber import (
    SegmentInfo,
    format_segments,
    format_timestamp_srt,
    load_audio_file,
    transcribe_file,
)


class TestTimestampAndFormatting:
    def test_format_timestamp_srt(self):
        assert format_timestamp_srt(0.0) == "00:00:00,000"
        assert format_timestamp_srt(5.25) == "00:00:05,250"
        assert format_timestamp_srt(65.432) == "00:01:05,432"
        assert format_timestamp_srt(3661.05) == "01:01:01,050"
        assert format_timestamp_srt(-1.0) == "00:00:00,000"

    def test_format_timestamp_srt_boundary_rollover(self):
        # 59.9996s must roll over into 1 minute, never 00:00:60,000
        assert format_timestamp_srt(59.9996) == "00:01:00,000"
        # 3599.9999s must roll over into 1 hour, never 00:59:60,000 or 00:60:00,000
        assert format_timestamp_srt(3599.9999) == "01:00:00,000"

    def test_format_segments_text(self):
        segments = [
            SegmentInfo(start=0.0, end=2.0, text="First sentence."),
            SegmentInfo(start=2.5, end=5.0, text="Second sentence."),
        ]
        text_out = format_segments(segments, output_format="text")
        assert text_out == "First sentence.\nSecond sentence."

    def test_format_segments_srt(self):
        segments = [
            SegmentInfo(start=1.0, end=3.5, text="Hello world"),
            SegmentInfo(start=4.0, end=6.0, text="Subtitle test"),
        ]
        srt_out = format_segments(segments, output_format="srt")
        assert "1\n00:00:01,000 --> 00:00:03,500\nHello world" in srt_out
        assert "2\n00:00:04,000 --> 00:00:06,000\nSubtitle test" in srt_out

    def test_format_segments_json(self):
        segments = [
            SegmentInfo(start=0.5, end=1.8, text="JSON test"),
        ]
        json_out = format_segments(segments, output_format="json")
        data = json.loads(json_out)
        assert len(data) == 1
        assert data[0]["id"] == 1
        assert data[0]["start"] == 0.5
        assert data[0]["end"] == 1.8
        assert data[0]["text"] == "JSON test"

    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Invalid output format"):
            format_segments([], output_format="unsupported_format")


class TestAudioFileLoading:
    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            load_audio_file("non_existent_audio_file.wav")

    def test_load_wav_file_mono_16bit(self, tmp_path):
        wav_path = tmp_path / "test_mono.wav"
        sr = 16000
        duration = 0.5
        samples = (
            np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration))) * 16000
        ).astype(np.int16)

        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sr)
            wf.writeframes(samples.tobytes())

        loaded = load_audio_file(wav_path)
        assert isinstance(loaded, np.ndarray)
        assert loaded.dtype == np.float32
        assert len(loaded) == len(samples)
        # Peak should be around 0.5
        assert 0.4 < np.max(np.abs(loaded)) < 0.6

    def test_load_wav_file_mono_24bit(self, tmp_path):
        wav_path = tmp_path / "test_mono_24bit.wav"
        # Signed 24-bit PCM values spanning negative, zero, and positive amplitudes.
        source_values = [-8388608, -4194304, 0, 4194304, 8388607]
        raw_bytes = b"".join(
            (value & 0xFFFFFF).to_bytes(3, byteorder="little", signed=False)
            for value in source_values
        )

        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(3)
            wf.setframerate(16000)
            wf.writeframes(raw_bytes)

        loaded = load_audio_file(wav_path)
        assert len(loaded) == len(source_values)
        expected = np.asarray(source_values, dtype=np.float32) / 8388608.0
        np.testing.assert_allclose(loaded, expected, atol=1e-6)

    def test_float_wav_reports_soundfile_requirement_when_unavailable(self, tmp_path):
        """Python wave rejects IEEE-float WAV; loader should explain fallback need."""
        wav_path = tmp_path / "float_audio.wav"
        # Minimal mono IEEE-float WAV: format tag 3, 32-bit samples.
        samples = np.asarray([0.25, -0.5], dtype="<f4")
        import struct

        fmt = struct.pack("<HHIIHH", 3, 1, 16000, 64000, 4, 32)
        data = samples.tobytes()
        chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt
        chunks += b"data" + struct.pack("<I", len(data)) + data
        wav_path.write_bytes(b"RIFF" + struct.pack("<I", len(chunks) + 4) + b"WAVE" + chunks)

        with (
            pytest.MonkeyPatch.context() as mp,
            pytest.raises(ValueError, match="unknown format: 3.*soundfile"),
        ):
            mp.setitem(sys.modules, "soundfile", None)
            load_audio_file(wav_path)

    def test_load_wav_file_mono_32bit(self, tmp_path):
        wav_path = tmp_path / "test_mono_32bit.wav"
        sr = 16000
        duration = 0.5
        # 32-bit signed int samples with peak around 0.5 (2**30)
        samples = (
            np.sin(2 * np.pi * 440 * np.linspace(0, duration, int(sr * duration))) * (2**30)
        ).astype(np.int32)

        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(4)
            wf.setframerate(sr)
            wf.writeframes(samples.tobytes())

        loaded = load_audio_file(wav_path)
        assert isinstance(loaded, np.ndarray)
        assert loaded.dtype == np.float32
        assert len(loaded) == len(samples)
        assert 0.4 < np.max(np.abs(loaded)) < 0.6


class TestTranscribeFileExecution:
    def test_transcribe_file_to_stdout_and_file(self, tmp_path):
        wav_path = tmp_path / "meeting.wav"
        # Create minimal 0.2s WAV
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(np.zeros(3200, dtype=np.int16).tobytes())

        # Mock engine with segments
        mock_engine = MagicMock()
        mock_seg = MagicMock()
        mock_seg.start = 0.0
        mock_seg.end = 2.0
        mock_seg.text = "Offline meeting transcription"

        mock_engine.model.transcribe.return_value = (iter([mock_seg]), MagicMock())
        mock_engine.beam_size = 5
        mock_engine.task = "transcribe"
        mock_engine.language = "en"

        out_file = tmp_path / "output.txt"
        res = transcribe_file(
            file_path=wav_path,
            output_format="text",
            output_path=out_file,
            engine=mock_engine,
        )

        assert res == "Offline meeting transcription"
        assert out_file.exists()
        assert out_file.read_text(encoding="utf-8") == "Offline meeting transcription"

    def test_transcribe_file_wires_model_registry(self, tmp_path):
        from unittest.mock import patch

        wav_path = tmp_path / "test.wav"
        with wave.open(str(wav_path), "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(np.zeros(1600, dtype=np.int16).tobytes())

        with (
            patch("kural.engine.whisper_engine.WhisperEngine") as mock_engine_cls,
            patch("kural.config.ConfigManager") as mock_cm_cls,
        ):
            mock_cm = MagicMock()
            mock_cm.get_whisper_config.return_value = {
                "model": "distil-large-v3.5",
                "models": {
                    "distil-large-v3.5": {
                        "source": "Systran/faster-distil-whisper-large-v3",
                        "group": "official",
                    }
                },
            }
            mock_cm_cls.return_value = mock_cm

            mock_engine_instance = MagicMock()
            mock_engine_instance.model = None
            mock_engine_instance.transcribe_audio.return_value = "transcribed"
            mock_engine_cls.return_value = mock_engine_instance

            res = transcribe_file(wav_path)
            assert res == "transcribed"

            # Verify model_registry was passed to WhisperEngine
            call_kwargs = mock_engine_cls.call_args.kwargs
            assert "model_registry" in call_kwargs
            registry = call_kwargs["model_registry"]
            assert registry is not None
            # Verify alias resolves to configured source
            assert (
                registry.get_source("distil-large-v3.5") == "Systran/faster-distil-whisper-large-v3"
            )
