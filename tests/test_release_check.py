"""Offline release gate regression tests."""

import importlib.util
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "release_check", Path(__file__).parents[1] / "packaging" / "release_check.py"
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


@pytest.mark.parametrize("tag", ["main", "", "--help", "v1.0", "v1.0.0\n", "v1.0.0/evil"])
def test_reject_non_tag_input(tag):
    with pytest.raises(ValueError):
        release.validate_tag(tag)


def test_exact_tag_commit_and_version(monkeypatch):
    monkeypatch.delenv("GITHUB_EVENT_NAME", raising=False)
    monkeypatch.setattr(
        release.subprocess,
        "check_output",
        lambda command, **kwargs: (
            '[project]\nversion="1.2.3"' if command[1] == "show" else "a" * 40
        ),
    )
    monkeypatch.setattr(release.subprocess, "run", lambda *args, **kwargs: None)
    assert release.validate_tag("v1.2.3") == ("a" * 40, "1.2.3")
    with pytest.raises(ValueError):
        release.validate_tag("v1.2.4")
    monkeypatch.setenv("GITHUB_EVENT_NAME", "push")
    assert release.validate_tag("v1.2.3")[0] == "a" * 40


def test_artifact_set_and_checksums(tmp_path):
    names = [
        "kural-1.2.3-py3-none-any.whl",
        "kural-1.2.3.tar.gz",
        "kural-windows-x64.zip",
        "kural-windows-x64-setup.exe",
    ]
    with pytest.raises(ValueError):
        release.checksums(tmp_path, "1.2.3")
    for name in names:
        (tmp_path / name).write_bytes(b"verified artifact")
    release.checksums(tmp_path, "1.2.3")
    assert len((tmp_path / "SHA256SUMS").read_text().splitlines()) == 4
    (tmp_path / "SHA256SUMS").unlink()
    (tmp_path / names[0]).write_bytes(b"")
    with pytest.raises(ValueError, match="Empty"):
        release.checksums(tmp_path, "1.2.3")
