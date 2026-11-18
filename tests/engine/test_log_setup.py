"""Tests for kural.engine.log_setup — rotating file handler and level config."""

import logging
from unittest.mock import MagicMock, patch

from kural.engine.log_setup import setup_logging


class TestLogSetup:
    def teardown_method(self):
        # Reset handlers after each test so tests stay isolated
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

    def test_setup_logging_installs_handlers_when_root_empty(self, tmp_path):
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        config = {
            "logging": {
                "level": "DEBUG",
                "log_transcriptions": False,
                "file": {
                    "enabled": True,
                    "filename": "test_kural.log",
                    "max_bytes": 512,
                    "backup_count": 2,
                },
            }
        }

        with patch("kural.engine.utils.get_user_app_data_path", return_value=str(tmp_path)):
            setup_logging(config)

        # Expect at least console + rotating file handler
        assert len(root.handlers) >= 2
        assert root.level == logging.DEBUG

        # Verify a log message writes to the rotating file
        logging.getLogger("test").info("hello test log")
        log_file = tmp_path / "test_kural.log"
        assert log_file.exists()
        assert "hello test log" in log_file.read_text(encoding="utf-8")

    def test_setup_logging_respects_file_disabled(self):
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        config = {
            "logging": {
                "level": "INFO",
                "file": {"enabled": False},
            }
        }

        setup_logging(config)
        # Only console handler installed
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0], logging.StreamHandler)

    def test_setup_logging_idempotent_when_handlers_exist(self):
        root = logging.getLogger()
        for h in list(root.handlers):
            root.removeHandler(h)

        mock_handler = MagicMock()
        root.addHandler(mock_handler)

        setup_logging({"logging": {"level": "WARNING"}})
        # Does not clobber existing handlers
        assert root.handlers == [mock_handler]
