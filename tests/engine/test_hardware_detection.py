"""Tests for kural.engine.hardware_detection — fully mocked so no GPU is required."""

from unittest.mock import MagicMock, patch

from kural.engine.hardware_detection import (
    detect_and_print,
    detect_gpu,
    missing_gpu_libraries,
)


class TestDetectGPU:
    def test_nvidia_detected_from_smi(self):
        fake_run = MagicMock()
        fake_run.returncode = 0
        fake_run.stdout = "NVIDIA GeForce RTX 3050 Laptop GPU\n"
        with patch("subprocess.run", return_value=fake_run):
            vendor, name = detect_gpu()
            assert vendor == "nvidia"
            assert "RTX 3050" in name

    def test_no_gpu_when_smi_fails(self):
        fake_run = MagicMock()
        fake_run.returncode = 1
        with patch("subprocess.run", return_value=fake_run):
            vendor, name = detect_gpu()
            assert vendor is None
            assert name is None

    def test_smi_not_found(self):
        with patch("subprocess.run", side_effect=FileNotFoundError):
            vendor, name = detect_gpu()
            assert vendor is None
            assert name is None


class TestMissingGpuLibraries:
    def test_returns_empty_when_all_load(self):
        with (
            patch("kural.engine.hardware_detection._detect_ct2_variant", return_value="cuda"),
            patch("kural.engine.hardware_detection._library_loads", return_value=True),
        ):
            missing = missing_gpu_libraries()
            assert missing == []

    def test_flags_missing_cublas_when_load_fails(self):
        def fake_load(name):
            # cublas fails, others succeed
            return "cublas" not in name

        with (
            patch("kural.engine.hardware_detection._detect_ct2_variant", return_value="cuda"),
            patch("kural.engine.hardware_detection._library_loads", side_effect=fake_load),
        ):
            missing = missing_gpu_libraries()
            assert "cublas64_12.dll" in missing


class TestDetectAndPrint:
    def test_detect_and_print_with_gpu(self):
        with (
            patch(
                "kural.engine.hardware_detection.detect_gpu",
                return_value=("nvidia", "NVIDIA GeForce RTX 3050"),
            ),
            patch(
                "kural.engine.hardware_detection.find_cuda_runtime",
                return_value="12.4",
            ),
            patch(
                "kural.engine.hardware_detection._detect_ct2_variant",
                return_value="cuda",
            ),
            patch(
                "kural.engine.hardware_detection.test_ct2_gpu",
                return_value=True,
            ),
        ):
            vendor, name, ok = detect_and_print("cuda")
            assert vendor == "nvidia"
            assert "RTX 3050" in name
            assert ok is True
