"""Tests for benchmarks module — pure unit tests, 0 GPU or network required."""

from unittest.mock import MagicMock

from benchmarks.datasets import BenchmarkSample, create_synthetic_wav, load_or_create_samples
from benchmarks.metrics import (
    character_error_rate,
    levenshtein_distance,
    normalize_text,
    real_time_factor,
    word_error_rate,
)
from benchmarks.run import format_markdown_report, run_benchmark_for_model


class TestLevenshteinDistance:
    def test_identical_sequences(self):
        assert levenshtein_distance("hello", "hello") == 0
        assert levenshtein_distance(["a", "b"], ["a", "b"]) == 0

    def test_single_insertion(self):
        assert levenshtein_distance("cat", "cats") == 1

    def test_single_deletion(self):
        assert levenshtein_distance("cats", "cat") == 1

    def test_single_substitution(self):
        assert levenshtein_distance("cat", "bat") == 1

    def test_empty_sequence(self):
        assert levenshtein_distance("", "test") == 4
        assert levenshtein_distance("test", "") == 4
        assert levenshtein_distance("", "") == 0


class TestTextNormalization:
    def test_punctuation_and_whitespace(self):
        text = "Hello, world!  This... is a test."
        norm = normalize_text(text)
        assert norm == "Hello world This is a test"

    def test_empty_text(self):
        assert normalize_text("") == ""
        assert normalize_text(None) == ""


class TestWordErrorRate:
    def test_exact_match_zero(self):
        assert word_error_rate("Hello world", "hello world") == 0.0

    def test_one_substitution(self):
        # 1 error in 4 words = 0.25
        assert word_error_rate("the quick brown fox", "the fast brown fox") == 0.25

    def test_punctuation_ignored(self):
        assert word_error_rate("Hello, world!", "hello world") == 0.0

    def test_empty_reference(self):
        assert word_error_rate("", "") == 0.0
        assert word_error_rate("", "extra words") == 1.0


class TestCharacterErrorRate:
    def test_exact_match_zero(self):
        assert character_error_rate("hello", "hello") == 0.0

    def test_tamil_exact_match(self):
        tamil_ref = "வணக்கம்"
        assert character_error_rate(tamil_ref, tamil_ref) == 0.0

    def test_tamil_single_char_diff(self):
        # வணக்கம் (hello) vs வணக்கம (missing pulli on last letter)
        ref = "வணக்கம்"
        hyp = "வணக்கம"
        cer = character_error_rate(ref, hyp)
        assert 0.0 < cer < 0.5

    def test_tamil_cer_calculation(self):
        # "குரல்" (Kural) vs "குரல"
        ref = "குரல்"
        hyp = "குரல"
        assert character_error_rate(ref, hyp) > 0.0


class TestRealTimeFactor:
    def test_rtf_calculation(self):
        # 1.0s processing for 4.0s audio -> RTF = 0.25
        assert real_time_factor(1.0, 4.0) == 0.25

    def test_zero_duration_safe(self):
        assert real_time_factor(1.0, 0.0) == 0.0


class TestDatasetLoader:
    def test_creates_synthetic_wav_and_manifest(self, tmp_path):
        samples = load_or_create_samples(tmp_path)
        assert len(samples) > 0
        assert (tmp_path / "manifest.json").exists()
        sample = samples[0]
        assert sample.audio_path.exists()
        assert sample.duration_sec > 0.0


class TestBenchmarkRunnerMocked:
    def test_run_benchmark_mocked_engine(self, tmp_path):
        # Create a small synthetic sample
        wav_path = tmp_path / "sample.wav"
        create_synthetic_wav(wav_path, duration_sec=1.0)
        sample = BenchmarkSample(
            sample_id="test_1",
            audio_path=wav_path,
            reference_text="hello world",
            language="en",
            duration_sec=1.0,
        )

        def mock_factory(model_key, device, compute_type):
            mock = MagicMock()
            mock.transcribe_audio.return_value = "hello world"
            return mock

        summary = run_benchmark_for_model(
            model_key="large-v3-turbo",
            device="cuda",
            compute_type="float16",
            samples=[sample],
            engine_factory=mock_factory,
        )

        assert summary.model_key == "large-v3-turbo"
        assert summary.avg_wer == 0.0
        assert summary.sample_count == 1

        md_report = format_markdown_report([summary])
        assert "Kural ASR Benchmark Report" in md_report
        assert "large-v3-turbo" in md_report
