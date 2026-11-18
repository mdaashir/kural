"""Tests for kural.selftest — offline mocked diagnostics for CI and testing."""

from unittest.mock import MagicMock, patch

import numpy as np

from kural.selftest import (
    _report,
    _test_audio_capture,
    _test_clipboard,
    _test_end_to_end,
    _test_model_loadable,
    run_selftest,
)


class TestSelftestStages:
    def test_audio_capture_success(self):
        fake_sd = MagicMock()
        fake_sd.query_devices.return_value = {"name": "Test Mic", "default_samplerate": 16000}
        # Buffer with non-zero RMS
        fake_recording = np.ones((8000, 1), dtype=np.float32) * 0.1
        fake_sd.rec.return_value = fake_recording

        with patch.dict("sys.modules", {"sounddevice": fake_sd}):
            ok, msg = _test_audio_capture()
            assert ok is True
            assert "Captured" in msg

    def test_audio_capture_silence_failure(self):
        fake_sd = MagicMock()
        fake_sd.query_devices.return_value = {"name": "Test Mic", "default_samplerate": 16000}
        # Pure silence buffer
        fake_recording = np.zeros((8000, 1), dtype=np.float32)
        fake_sd.rec.return_value = fake_recording

        with patch.dict("sys.modules", {"sounddevice": fake_sd}):
            ok, (reason, fix) = _test_audio_capture()
            assert ok is False
            assert "pure silence" in reason
            assert "Windows Settings" in fix

    def test_audio_capture_device_query_error(self):
        fake_sd = MagicMock()
        fake_sd.query_devices.side_effect = RuntimeError("No audio hardware")

        with patch.dict("sys.modules", {"sounddevice": fake_sd}):
            ok, (reason, fix) = _test_audio_capture()
            assert ok is False
            assert "No default input audio device" in reason

    def test_model_loadable_cached(self):
        fake_reg = MagicMock()
        fake_reg.is_model_cached.return_value = True

        with (
            patch("kural.engine.model_registry.ModelRegistry", return_value=fake_reg),
            patch("kural.config.ConfigManager") as mock_cm,
        ):
            mock_cm.return_value.get_whisper_config.return_value = {
                "model": "large-v3-turbo",
                "device": "cuda",
            }
            ok, msg = _test_model_loadable()
            assert ok is True
            assert "cached locally" in msg

    def test_end_to_end_transcription_success(self):
        fake_engine = MagicMock()
        fake_engine.transcribe_audio.return_value = "transcribed"

        with (
            patch("kural.engine.whisper_engine.WhisperEngine", return_value=fake_engine),
            patch("kural.config.ConfigManager") as mock_cm,
        ):
            mock_cm.return_value.get_whisper_config.return_value = {
                "model": "large-v3-turbo",
                "device": "cuda",
                "compute_type": "float16",
            }
            ok, msg = _test_end_to_end()
            assert ok is True
            assert "Inference pipeline verified" in msg

    def test_end_to_end_transcription_failure(self):
        fake_engine = MagicMock()
        fake_engine.transcribe_audio.side_effect = RuntimeError("CUDA driver missing")

        with (
            patch("kural.engine.whisper_engine.WhisperEngine", return_value=fake_engine),
            patch("kural.config.ConfigManager"),
        ):
            ok, (reason, fix) = _test_end_to_end()
            assert ok is False
            assert "CUDA driver missing" in reason

    def test_clipboard_round_trip_success(self):
        fake_pyperclip = MagicMock()
        stored = ["original_text"]

        def mock_copy(txt):
            stored[0] = txt

        def mock_paste():
            return stored[0]

        fake_pyperclip.copy.side_effect = mock_copy
        fake_pyperclip.paste.side_effect = mock_paste

        with patch.dict("sys.modules", {"pyperclip": fake_pyperclip}):
            ok, msg = _test_clipboard()
            assert ok is True
            assert "round-trip verified" in msg
            # Check original content restored
            assert stored[0] == "original_text"

    def test_clipboard_mismatch_failure(self):
        fake_pyperclip = MagicMock()
        fake_pyperclip.paste.return_value = "interfering_clipboard_app"

        with patch.dict("sys.modules", {"pyperclip": fake_pyperclip}):
            ok, (reason, fix) = _test_clipboard()
            assert ok is False
            assert "did not round-trip" in reason


class TestRunSelftestSuite:
    def test_all_stages_pass_returns_zero(self):
        with (
            patch("kural.selftest._test_audio_capture", return_value=(True, "Audio OK")),
            patch("kural.selftest._test_model_loadable", return_value=(True, "Model OK")),
            patch("kural.selftest._test_end_to_end", return_value=(True, "End-to-End OK")),
            patch("kural.selftest._test_clipboard", return_value=(True, "Clipboard OK")),
        ):
            code = run_selftest()
            assert code == 0

    def test_any_stage_fail_returns_one(self):
        with (
            patch(
                "kural.selftest._test_audio_capture", return_value=(False, ("Mic muted", "Fix mic"))
            ),
            patch("kural.selftest._test_model_loadable", return_value=(True, "Model OK")),
            patch("kural.selftest._test_end_to_end", return_value=(True, "End-to-End OK")),
            patch("kural.selftest._test_clipboard", return_value=(True, "Clipboard OK")),
        ):
            code = run_selftest()
            assert code == 1

    def test_report_helper_aggregates_failures(self):
        failures = []
        _report(True, "Passed message", failures, "test-stage")
        assert len(failures) == 0

        _report(False, ("Reason message", "Fix hint"), failures, "fail-stage")
        assert len(failures) == 1
        assert failures[0] == ("fail-stage", "Reason message", "Fix hint")
