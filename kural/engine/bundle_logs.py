# MIT License — Copyright (c) 2025 drajb (upstream: Pin Wang / whisper-key-local)
# Ported and adapted from drajb/whisper-local/src/whisper_key/bundle_logs.py
"""Creates a redacted diagnostic zip archive for bug reports and troubleshooting.

Users running `kural --bundle-logs` get a single sanitized zip file that can be
safely shared or attached to GitHub issues without manually scrubbing usernames,
file paths, emails, or custom vocabulary hotwords.

Bundles:
- about.txt: build metadata, Python version, OS platform
- doctor.txt: live output of `kural --doctor`
- kural.log: last 500 lines of the active rotating log + rotated logs
- user_settings.yaml: active configuration (with hotwords and prompts masked)
"""

import datetime
import io
import logging
import re
import sys
import zipfile
from pathlib import Path

from kural.engine.utils import get_user_app_data_path, get_version

logger = logging.getLogger(__name__)

# Regex pairs applied across every file before writing to zip
_REDACTIONS = [
    (re.compile(r"(C:\\Users\\)([^\\]+)", re.IGNORECASE), r"\1<USER>"),
    (re.compile(r"(C:/Users/)([^/]+)", re.IGNORECASE), r"\1<USER>"),
    (re.compile(r"(/Users/)([^/]+)"), r"\1<USER>"),
    (re.compile(r"(/home/)([^/]+)"), r"\1<USER>"),
    (
        re.compile(r"(\bhttps?://)[^/\s:@]+:[^/\s@]+@", re.IGNORECASE),
        r"\1<REDACTED>@",
    ),
    (
        re.compile(
            r"([?&](?:token|key|api[_-]?key|password|secret|access[_-]?token)=)[^&\s]+",
            re.IGNORECASE,
        ),
        r"\1<REDACTED>",
    ),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "<EMAIL>"),
]

# Sensitive configuration fields scrubbed specifically from YAML files
_YAML_REDACTIONS = [
    (re.compile(r"(^\s*hotwords\s*:\s*)\[[^\]]*\]", re.MULTILINE), r"\1[<REDACTED>]"),
    (re.compile(r"(^\s*hotwords\s*:\s*)\n(\s*-\s.*\n?)+", re.MULTILINE), r"\1 [<REDACTED>]\n"),
    (re.compile(r"(^\s*endpoint\s*:\s*).+$", re.MULTILINE), r"\1<REDACTED>"),
    (re.compile(r"(^\s*initial_prompt\s*:\s*).+$", re.MULTILINE), r"\1<REDACTED>"),
]


def redact_text(text: str) -> str:
    """Scrub usernames, paths, emails, and credentials from log text."""
    for pattern, replacement in _REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def redact_yaml(text: str) -> str:
    """Mask sensitive fields (hotwords, prompts, endpoints) in YAML configuration."""
    for pattern, replacement in _YAML_REDACTIONS:
        text = pattern.sub(replacement, text)
    return text


def _build_about() -> str:
    """Generate diagnostic header metadata."""
    now = datetime.datetime.now().isoformat()
    return (
        "Kural Diagnostic Bundle\n"
        f"Generated: {now}\n"
        f"Version: {get_version()}\n"
        f"Python: {sys.version}\n"
        f"Platform: {sys.platform}\n\n"
        "Contents:\n"
        "  about.txt           — this metadata file\n"
        "  doctor.txt          — output of `kural --doctor` (redacted)\n"
        "  kural.log           — last ~500 lines of active rotating log (redacted)\n"
        "  user_settings.yaml  — active user settings (hotwords & prompts masked)\n\n"
        "Privacy Notice:\n"
        "  Windows/POSIX usernames in file paths, email addresses, URL credentials,\n"
        "  and custom dictionary hotwords have been replaced with placeholders.\n"
        "  Transcribed speech text is never logged unless debug mode was explicitly enabled.\n"
    )


def _capture_doctor() -> str:
    """Run `kural --doctor` and capture output into a string."""
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        from kural.doctor import run_doctor

        run_doctor()
    except Exception as e:
        buf.write(f"\n[bundle-logs: doctor error: {e}]\n")
    finally:
        sys.stdout = old_stdout
    return redact_text(buf.getvalue())


def _tail_lines(path: Path, n: int = 500) -> str:
    """Read the last N lines of a file safely."""
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
        return "".join(lines[-n:])
    except Exception as e:
        return f"[bundle-logs: could not read {path}: {e}]\n"


def bundle_logs(output_path: str | None = None) -> int:
    """Build a sanitized zip archive containing diagnostic logs and configuration.

    Args:
        output_path: Custom zip file destination path. When None, writes to the
                     current working directory with a timestamped filename.

    Returns:
        0 on completion.
    """
    app_data = Path(get_user_app_data_path())

    if not output_path:
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        output_path = str(Path.cwd() / f"kural-bundle-{stamp}.zip")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    bundled: list[str] = []
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("about.txt", _build_about())
        bundled.append("about.txt")

        zf.writestr("doctor.txt", _capture_doctor())
        bundled.append("doctor.txt")

        log_path = app_data / "kural.log"
        if log_path.exists():
            tail = _tail_lines(log_path, 500)
            zf.writestr("kural.log", redact_text(tail))
            bundled.append("kural.log")

        # Collect up to 2 rotated logs if present (e.g. kural.log.1, kural.log.2)
        for older in sorted(app_data.glob("kural.log.*"))[-2:]:
            try:
                content = older.read_text(encoding="utf-8", errors="replace")
                zf.writestr(older.name, redact_text(content))
                bundled.append(older.name)
            except Exception:
                pass

        settings_path = app_data / "user_settings.yaml"
        if settings_path.exists():
            try:
                raw_yaml = settings_path.read_text(encoding="utf-8", errors="replace")
                zf.writestr("user_settings.yaml", redact_yaml(redact_text(raw_yaml)))
                bundled.append("user_settings.yaml")
            except Exception:
                pass

    print(f"\n📦 Diagnostic bundle written to: {output}")
    print(f"   {len(bundled)} file(s) included:")
    for f in bundled:
        print(f"   • {f}")
    print("\n   ℹ Redacted: usernames in paths, emails, credentials, and custom hotwords.")
    print("   ℹ Safe to attach directly to GitHub bug reports or issues.\n")
    return 0
