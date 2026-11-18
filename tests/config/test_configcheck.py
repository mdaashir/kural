"""Tests for kural.config.configcheck — schema validation, bounds checking, and auto-repair."""

from kural.config.configcheck import validate_config


class TestConfigValidation:
    def test_valid_config_passes_without_issues(self):
        cfg = {
            "whisper": {
                "device": "cuda",
                "compute_type": "float16",
                "backend": "faster_whisper",
                "idle_unload_minutes": 5,
                "beam_size": 5,
            },
            "hotkey": {
                "recording_mode": "toggle",
                "recording_hotkey": "ctrl+space",
            },
            "overlay": {
                "position": "bottom-center",
            },
            "audio": {
                "max_duration": 30,
            },
        }
        clean, issues = validate_config(cfg)
        assert issues == []
        assert clean["whisper"]["device"] == "cuda"
        assert clean["whisper"]["compute_type"] == "float16"

    def test_invalid_device_falls_back_to_cuda(self):
        cfg = {"whisper": {"device": "invalid_gpu"}}
        clean, issues = validate_config(cfg)
        assert len(issues) == 1
        assert "Invalid whisper.device" in issues[0]
        assert clean["whisper"]["device"] == "cuda"

    def test_invalid_compute_type_falls_back_to_float16(self):
        cfg = {"whisper": {"compute_type": "int4_unknown"}}
        clean, issues = validate_config(cfg)
        assert len(issues) == 1
        assert "Invalid whisper.compute_type" in issues[0]
        assert clean["whisper"]["compute_type"] == "float16"

    def test_negative_idle_unload_clamped_to_zero(self):
        cfg = {"whisper": {"idle_unload_minutes": -10}}
        clean, issues = validate_config(cfg)
        assert len(issues) == 1
        assert "cannot be negative" in issues[0]
        assert clean["whisper"]["idle_unload_minutes"] == 0

    def test_out_of_bounds_beam_size_clamped(self):
        cfg = {"whisper": {"beam_size": 50}}
        clean, issues = validate_config(cfg)
        assert len(issues) == 1
        assert "clamped to 10" in issues[0]
        assert clean["whisper"]["beam_size"] == 10

    def test_invalid_recording_mode_falls_back(self):
        cfg = {"hotkey": {"recording_mode": "voice_activated_unknown"}}
        clean, issues = validate_config(cfg)
        assert len(issues) == 1
        assert "Falling back to 'toggle'" in issues[0]
        assert clean["hotkey"]["recording_mode"] == "toggle"

    def test_audio_duration_clamped_to_safe_bounds(self):
        cfg = {"audio": {"max_duration": 1000}}
        clean, issues = validate_config(cfg)
        assert len(issues) == 1
        assert "clamped to 300" in issues[0]
        assert clean["audio"]["max_duration"] == 300

    def test_invalid_indic_script_falls_back(self):
        cfg = {"whisper": {"indic_script": "latin_invalid"}}
        clean, issues = validate_config(cfg)
        assert len(issues) == 1
        assert "Invalid whisper.indic_script" in issues[0]
        assert clean["whisper"]["indic_script"] == "native"

    def test_noise_suppression_strength_clamped(self):
        cfg = {"audio": {"noise_suppression": {"strength": 2.5}}}
        clean, issues = validate_config(cfg)
        assert len(issues) == 1
        assert "clamped to 1.0" in issues[0]
        assert clean["audio"]["noise_suppression"]["strength"] == 1.0

    def test_ducking_factor_clamped(self):
        cfg = {"audio": {"ducking": {"factor": 1.5}}}
        clean, issues = validate_config(cfg)
        assert len(issues) == 1
        assert "clamped to 1.0" in issues[0]
        assert clean["audio"]["ducking"]["factor"] == 1.0
