"""Evaluation metrics for ASR benchmarks: WER, CER, RTF, and timing statistics."""

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass


def levenshtein_distance[T](seq1: Sequence[T], seq2: Sequence[T]) -> int:
    """Compute the minimum edit distance (insertions, deletions, substitutions) between two sequences.

    Uses dynamic programming with O(min(m, n)) space.
    """
    if len(seq1) < len(seq2):
        seq1, seq2 = seq2, seq1

    if len(seq2) == 0:
        return len(seq1)

    previous_row = list(range(len(seq2) + 1))
    for i, c1 in enumerate(seq1):
        current_row = [i + 1] * (len(seq2) + 1)
        for j, c2 in enumerate(seq2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (0 if c1 == c2 else 1)
            current_row[j + 1] = min(insertions, deletions, substitutions)
        previous_row = current_row

    return previous_row[-1]


def normalize_text(text: str) -> str:
    """Normalize text for consistent comparison across Unicode, case, and whitespace."""
    if not text:
        return ""
    # Unicode NFKC normalization decomposes ligatures and standardizes codepoints
    text = unicodedata.normalize("NFKC", text)
    # Strip terminal punctuation commonly added/removed by Whisper
    text = re.sub(r"[\.,!?:;\"'«»\(\)\[\]{}—–\-]+", " ", text)
    # Collapse multiple whitespaces
    return " ".join(text.strip().split())


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate (WER) = (S + D + I) / N.

    Returns float from 0.0 (exact match) upwards (can exceed 1.0 on heavy insertions).
    """
    ref_norm = normalize_text(reference).lower()
    hyp_norm = normalize_text(hypothesis).lower()

    ref_words = ref_norm.split()
    hyp_words = hyp_norm.split()

    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    distance = levenshtein_distance(ref_words, hyp_words)
    return distance / len(ref_words)


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Compute Character Error Rate (CER) = (S + D + I) / N.

    Crucial for Indic/Tamil scripts where word-level tokenization can be distorted
    by agglutination and Unicode grapheme cluster representation.
    """
    ref_norm = normalize_text(reference).lower()
    hyp_norm = normalize_text(hypothesis).lower()

    # Compare character sequences without whitespace
    ref_chars = [c for c in ref_norm if not c.isspace()]
    hyp_chars = [c for c in hyp_norm if not c.isspace()]

    if not ref_chars:
        return 0.0 if not hyp_chars else 1.0

    distance = levenshtein_distance(ref_chars, hyp_chars)
    return distance / len(ref_chars)


def real_time_factor(processing_time_sec: float, audio_duration_sec: float) -> float:
    """Compute Real-Time Factor (RTF) = processing_time / audio_duration.

    RTF < 1.0 means faster than real-time. RTF < 0.3 is target for interactive voice typing.
    """
    if audio_duration_sec <= 0:
        return 0.0
    return processing_time_sec / audio_duration_sec


@dataclass
class SampleResult:
    """Benchmark result for a single audio sample."""

    sample_id: str
    language: str
    audio_duration_sec: float
    inference_time_sec: float
    rtf: float
    wer: float
    cer: float
    reference_text: str
    hypothesis_text: str


@dataclass
class ModelBenchmarkSummary:
    """Aggregated benchmark statistics for a model configuration."""

    model_key: str
    device: str
    compute_type: str
    language: str
    sample_count: int
    total_audio_sec: float
    total_inference_sec: float
    avg_inference_sec: float
    avg_rtf: float
    avg_wer: float
    avg_cer: float
    sample_results: list[SampleResult]
