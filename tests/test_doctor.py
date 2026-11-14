"""Tests for kural.doctor — unit-testing health-check logic with mocks."""

from unittest.mock import patch

from kural.doctor import (
    Check,
    _section_config,
    _section_dependencies,
    _section_gpu,
    _section_runtime,
    run_doctor,
)


class TestCheck:
    def test_check_ok(self):
        c = Check("Sample").ok("detail")
        assert "[OK]" in c.status
        assert c.detail == "detail"

    def test_check_fail(self):
        c = Check("Sample").fail("broken")
        assert "[X]" in c.status

    def test_check_warn(self):
        c = Check("Sample").warn("careful")
        assert "[!]" in c.status

    def test_check_info(self):
        c = Check("Sample").info("note")
        assert "[i]" in c.status


class TestDoctorSections:
    def test_section_runtime_passes(self):
        failures = _section_runtime()
        assert failures == 0

    def test_section_dependencies_passes(self):
        failures = _section_dependencies()
        assert failures == 0

    def test_section_gpu_mocked(self):
        with (
            patch(
                "kural.engine.hardware_detection.detect_gpu", return_value=("nvidia", "RTX 3050")
            ),
            patch("kural.engine.hardware_detection.find_cuda_runtime", return_value="12.4"),
            patch("kural.engine.hardware_detection.missing_gpu_libraries", return_value=[]),
        ):
            failures = _section_gpu()
            assert failures == 0

    def test_section_config_passes(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        failures = _section_config()
        assert failures == 0

    def test_run_doctor_clean_returns_zero(self, tmp_path, monkeypatch):
        monkeypatch.setenv("APPDATA", str(tmp_path))
        with (
            patch(
                "kural.engine.hardware_detection.detect_gpu", return_value=("nvidia", "RTX 3050")
            ),
            patch("kural.engine.hardware_detection.find_cuda_runtime", return_value="12.4"),
            patch("kural.engine.hardware_detection.missing_gpu_libraries", return_value=[]),
        ):
            exit_code = run_doctor()
            assert exit_code == 0
