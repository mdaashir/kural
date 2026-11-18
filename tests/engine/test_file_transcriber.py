"""Tests for kural.engine.file_transcriber — offline audio file transcription CLI."""

import json
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
