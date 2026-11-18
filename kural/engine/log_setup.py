# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/log_setup.py
"""Configure Python logging for Kural: rotating file handler + console.

Called once from __main__.py before the runtime starts. Reads settings from the
merged config (logging.level, logging.file.*). Transcribed speech text is never
written to the log — the log_transcriptions flag is enforced at the call site in
kural/runtime.py and is not toggled here.
"""

import logging
import logging.handlers
import sys
from pathlib import Path


def setup_logging(config: dict | None = None) -> None:
    """Configure root logger with console + optional rotating file handler.

    Args:
        config: merged Kural config dict (kural/config/config.defaults.yaml shape).
                When None, uses sensible defaults: INFO to console only.
    """
    cfg = config or {}
    log_cfg = cfg.get("logging") or {}

    level_name: str = str(log_cfg.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    root = logging.getLogger()
    # Only configure once; skip if handlers already installed (e.g. in tests)
    if root.handlers:
        return

    root.setLevel(level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler — always present, writes to stderr
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    # Rotating file handler — opt-in via config
    file_cfg = log_cfg.get("file") or {}
    if file_cfg.get("enabled", True):
        try:
            from kural.engine.utils import get_user_app_data_path

            log_dir = Path(get_user_app_data_path())
            log_dir.mkdir(parents=True, exist_ok=True)

            filename = str(file_cfg.get("filename", "kural.log"))
            log_path = log_dir / filename
            max_bytes = int(file_cfg.get("max_bytes", 1_048_576))  # 1 MB
            backup_count = int(file_cfg.get("backup_count", 3))

            file_handler = logging.handlers.RotatingFileHandler(
                log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)

            # Emit one startup marker so the log is easy to tail
            logging.getLogger("kural.log_setup").info(
                "Logging started — %s (level=%s, max_bytes=%d, backups=%d)",
                log_path,
                level_name,
                max_bytes,
                backup_count,
            )
        except Exception as exc:
            # Non-fatal: fall back gracefully to console-only logging
            logging.getLogger("kural.log_setup").warning(
                "Could not create rotating log file: %s", exc
            )
