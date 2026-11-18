"""Tests for kural.engine.bundle_logs — PII redaction and diagnostic zip creation."""

import zipfile
from unittest.mock import patch

from kural.engine.bundle_logs import (
    bundle_logs,
    redact_text,
    redact_yaml,
)


class TestTextRedaction:
    def test_redact_windows_paths(self):
        text = r"Error reading file C:\Users\Alice\AppData\Roaming\kural\config.yaml"
        redacted = redact_text(text)
        assert r"C:\Users\<USER>\AppData\Roaming\kural\config.yaml" in redacted
        assert "Alice" not in redacted

    def test_redact_windows_forward_slash_paths(self):
        text = "file:///C:/Users/Bob/Downloads/Projects/kural"
        redacted = redact_text(text)
        assert "C:/Users/<USER>/Downloads/Projects/kural" in redacted
        assert "Bob" not in redacted

    def test_redact_posix_paths(self):
        text = "Loading from /home/charlie/.config/kural and /Users/david/repo"
        redacted = redact_text(text)
        assert "/home/<USER>/.config/kural" in redacted
        assert "/Users/<USER>/repo" in redacted
        assert "charlie" not in redacted
        assert "david" not in redacted

    def test_redact_emails(self):
        text = "Contact support at user.name+tag@example.com for help"
        redacted = redact_text(text)
        assert "<EMAIL>" in redacted
        assert "user.name" not in redacted

    def test_redact_url_credentials(self):
        text = "Connecting to https://admin:supersecret123@myhost.local:8080/v1"
        redacted = redact_text(text)
        assert "https://<REDACTED>@myhost.local:8080/v1" in redacted
        assert "supersecret123" not in redacted

    def test_redact_query_param_secrets(self):
        text = "GET /api?token=abc123secret&api_key=key9876&normal_param=42"
        redacted = redact_text(text)
        assert "token=<REDACTED>" in redacted
        assert "api_key=<REDACTED>" in redacted
        assert "normal_param=42" in redacted
        assert "abc123secret" not in redacted


class TestYamlRedaction:
    def test_redact_yaml_hotwords_inline(self):
        yaml_content = (
            "whisper:\n  hotwords: [Aashir, Kural, SecretProject]\n  model: large-v3-turbo"
        )
        redacted = redact_yaml(yaml_content)
        assert "hotwords: [<REDACTED>]" in redacted
        assert "Aashir" not in redacted
        assert "large-v3-turbo" in redacted

    def test_redact_yaml_initial_prompt(self):
        yaml_content = "whisper:\n  initial_prompt: 'Confidential custom prompt instructions'\n"
        redacted = redact_yaml(yaml_content)
        assert "initial_prompt: <REDACTED>" in redacted
        assert "Confidential" not in redacted


class TestBundleLogsArchive:
    def test_bundle_logs_creates_valid_zip(self, tmp_path):
        app_data = tmp_path / "app_data"
        app_data.mkdir()

        # Create dummy log and settings with PII
        log_file = app_data / "kural.log"
        log_file.write_text(
            r"2026-11-18 INFO Loaded from C:\Users\DeveloperName\kural.log with user@domain.com",
            encoding="utf-8",
        )

        settings_file = app_data / "user_settings.yaml"
        settings_file.write_text(
            "whisper:\n  hotwords: [PrivateCodeword]\n  model: large-v3-turbo\n",
            encoding="utf-8",
        )

        out_zip = tmp_path / "diagnostics_test.zip"

        with (
            patch("kural.engine.bundle_logs.get_user_app_data_path", return_value=str(app_data)),
            patch("kural.engine.bundle_logs._capture_doctor", return_value="Doctor output: All OK"),
        ):
            code = bundle_logs(str(out_zip))
            assert code == 0
            assert out_zip.exists()

        # Inspect zip contents
        with zipfile.ZipFile(out_zip, "r") as zf:
            names = zf.namelist()
            assert "about.txt" in names
            assert "doctor.txt" in names
            assert "kural.log" in names
            assert "user_settings.yaml" in names

            bundled_log = zf.read("kural.log").decode("utf-8")
            assert "DeveloperName" not in bundled_log
            assert "<USER>" in bundled_log
            assert "<EMAIL>" in bundled_log

            bundled_yaml = zf.read("user_settings.yaml").decode("utf-8")
            assert "PrivateCodeword" not in bundled_yaml
            assert "<REDACTED>" in bundled_yaml
