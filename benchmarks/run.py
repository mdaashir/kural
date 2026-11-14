"""CLI Benchmark runner for Whisper models on Kural.

Evaluates latency (RTF / seconds) and accuracy (WER / CER) on English and Tamil audio.
Usage:
    python -m benchmarks.run --models large-v3-turbo --device cuda --compute-type float16
"""

import argparse
import json
import logging
import sys
import time
import wave
from pathlib import Path

import numpy as np

from benchmarks.datasets import BenchmarkSample, load_or_create_samples
from benchmarks.metrics import (
    ModelBenchmarkSummary,
    SampleResult,
    character_error_rate,
    real_time_factor,
    word_error_rate,
)

logger = logging.getLogger("kural.benchmark")


def read_wav_as_float32(wav_path: Path | str) -> np.ndarray:
    """Read a mono 16 kHz WAV file into a float32 numpy array normalized to [-1.0, 1.0]."""
    with wave.open(str(wav_path), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    if rate != 16000:
        logger.warning(f"Audio file {wav_path} is at {rate} Hz, Whisper prefers 16000 Hz")

    if sampwidth == 2:
        audio = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    elif sampwidth == 4:
        audio = np.frombuffer(frames, dtype=np.float32)
    else:
        raise ValueError(f"Unsupported sample width: {sampwidth} bytes in {wav_path}")

    if n_channels > 1:
        audio = audio.reshape(-1, n_channels).mean(axis=1)

    return audio


def run_benchmark_for_model(
    model_key: str,
    device: str,
    compute_type: str,
    samples: list[BenchmarkSample],
    engine_factory=None,
) -> ModelBenchmarkSummary:
    """Benchmark a single model configuration across the provided audio samples."""
    print(f"\n⚡ Benchmarking [{model_key}] on {device} ({compute_type})...")

    # Use custom engine factory (e.g. for mocked tests) or standard WhisperEngine
    if engine_factory is not None:
        engine = engine_factory(model_key=model_key, device=device, compute_type=compute_type)
    else:
        from kural.engine.whisper_engine import WhisperEngine

        engine = WhisperEngine(
            model_key=model_key,
            device=device,
            compute_type=compute_type,
            language=None,  # auto per sample
        )

    results: list[SampleResult] = []

    for sample in samples:
        audio_data = read_wav_as_float32(sample.audio_path)
        # Set engine language for this sample
        engine.language = sample.language

        # Warm-up / measure inference
        t0 = time.perf_counter()
        hypothesis = engine.transcribe_audio(audio_data) or ""
        inference_time = time.perf_counter() - t0

        rtf = real_time_factor(inference_time, sample.duration_sec)
        wer = word_error_rate(sample.reference_text, hypothesis)
        cer = character_error_rate(sample.reference_text, hypothesis)

        result = SampleResult(
            sample_id=sample.sample_id,
            language=sample.language,
            audio_duration_sec=sample.duration_sec,
            inference_time_sec=inference_time,
            rtf=rtf,
            wer=wer,
            cer=cer,
            reference_text=sample.reference_text,
            hypothesis_text=hypothesis,
        )
        results.append(result)

        print(
            f"   [{sample.sample_id:18s}] "
            f"Dur: {sample.duration_sec:4.1f}s | "
            f"Inf: {inference_time:4.2f}s | "
            f"RTF: {rtf:5.3f} | "
            f"WER: {wer:5.2f} | "
            f"CER: {cer:5.2f}"
        )

    total_audio = sum(r.audio_duration_sec for r in results)
    total_inf = sum(r.inference_time_sec for r in results)
    avg_inf = total_inf / len(results) if results else 0.0
    avg_rtf = sum(r.rtf for r in results) / len(results) if results else 0.0
    avg_wer = sum(r.wer for r in results) / len(results) if results else 0.0
    avg_cer = sum(r.cer for r in results) / len(results) if results else 0.0

    return ModelBenchmarkSummary(
        model_key=model_key,
        device=device,
        compute_type=compute_type,
        language="mixed",
        sample_count=len(results),
        total_audio_sec=total_audio,
        total_inference_sec=total_inf,
        avg_inference_sec=avg_inf,
        avg_rtf=avg_rtf,
        avg_wer=avg_wer,
        avg_cer=avg_cer,
        sample_results=results,
    )


def format_markdown_report(summaries: list[ModelBenchmarkSummary]) -> str:
    """Format benchmark summaries into a GitHub-compatible Markdown comparison report."""
    lines = [
        "# Kural ASR Benchmark Report",
        "",
        "Evaluation of candidate Whisper models on target hardware (**Windows 11, NVIDIA RTX 3050 6 GB**).",
        "",
        "| Model | Device | Precision | Samples | Avg Latency | Avg RTF | Avg WER | Avg CER |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for s in summaries:
        lines.append(
            f"| `{s.model_key}` | {s.device.upper()} | `{s.compute_type}` | {s.sample_count} | "
            f"{s.avg_inference_sec:.2f}s | **{s.avg_rtf:.3f}** | {s.avg_wer * 100:.1f}% | {s.avg_cer * 100:.1f}% |"
        )

    lines.extend(
        [
            "",
            "### Notes & Interpretation",
            "- **RTF < 0.3**: Ideal for interactive, low-latency dictation.",
            "- **CER**: Character Error Rate is the primary metric for agglutinative Tamil text.",
            "- **WER**: Word Error Rate represents whole-word recognition accuracy.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Kural Whisper Model Benchmark Harness")
    parser.add_argument(
        "--models",
        nargs="+",
        default=["large-v3-turbo"],
        help="Model keys to benchmark (e.g. large-v3-turbo large-v3 distil-large-v3.5)",
    )
    parser.add_argument(
        "--device",
        choices=["cuda", "cpu"],
        default="cuda",
        help="Inference device (cuda or cpu)",
    )
    parser.add_argument(
        "--compute-type",
        choices=["float16", "int8", "float32"],
        default=None,
        help="Precision type (defaults to float16 on cuda, int8 on cpu)",
    )
    parser.add_argument(
        "--languages",
        nargs="+",
        default=None,
        help="Filter samples by language (e.g. en ta)",
    )
    parser.add_argument(
        "--samples-dir",
        type=str,
        default=None,
        help="Custom path containing audio samples and manifest.json",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Path to save detailed benchmark results as JSON",
    )
    parser.add_argument(
        "--report",
        type=str,
        default=None,
        help="Path to save the Markdown summary report",
    )

    args = parser.parse_args()

    # Determine default compute type if not specified
    compute_type = args.compute_type
    if compute_type is None:
        compute_type = "float16" if args.device == "cuda" else "int8"

    # Load audio samples
    samples = load_or_create_samples(args.samples_dir)
    if args.languages:
        langs = set(args.languages)
        samples = [s for s in samples if s.language in langs]

    if not samples:
        print("❌ No matching benchmark samples found.")
        return 1

    print(f"Loaded {len(samples)} benchmark sample(s).")

    summaries = []
    for model_key in args.models:
        summary = run_benchmark_for_model(
            model_key=model_key,
            device=args.device,
            compute_type=compute_type,
            samples=samples,
        )
        summaries.append(summary)

    # Print markdown report
    report_md = format_markdown_report(summaries)
    print("\n" + report_md)

    if args.report:
        report_path = Path(args.report)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report_md, encoding="utf-8")
        print(f"\n✓ Markdown report written to {report_path}")

    if args.output_json:
        json_path = Path(args.output_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        # Convert dataclasses to dicts
        import dataclasses

        raw_data = [dataclasses.asdict(s) for s in summaries]
        json_path.write_text(json.dumps(raw_data, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"✓ JSON benchmark data written to {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
