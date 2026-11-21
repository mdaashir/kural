"""Offline release gate regression tests."""

import importlib.util
from pathlib import Path

import pytest
from ruamel.yaml import YAML

SPEC = importlib.util.spec_from_file_location(
    "release_check", Path(__file__).parents[1] / "packaging" / "release_check.py"
)
release = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(release)


@pytest.mark.parametrize("tag", ["main", "", "--help", "v1.0", "v1.0.0\n", "v1.0.0/evil"])
def test_reject_non_tag_input(tag):
    with pytest.raises(ValueError):
        release.validate_tag(tag)


def test_pypi_publish_workflow_is_oidc_gated_and_uses_cmd_kural(tmp_path):
    workflow = (Path(__file__).parents[1] / ".github" / "workflows" / "publish-pypi.yml").read_text(
        encoding="utf-8"
    )
    assert "vars.PUBLISH_PYPI == 'true'" in workflow
    assert "workflow_dispatch" in workflow
    assert "permissions:\n      id-token: write" in workflow
    assert "environment:\n      name: pypi" in workflow
    assert "https://pypi.org/project/cmd-kural/" in workflow
    assert "pypa/gh-action-pypi-publish@release/v1" in workflow
    assert "api-token" not in workflow.lower()


def test_pypi_publish_sets_up_uv_before_uvx():
    workflows = Path(__file__).parents[1] / ".github" / "workflows"
    yaml = YAML(typ="safe")
    publish = yaml.load((workflows / "publish-pypi.yml").read_text(encoding="utf-8"))
    build = yaml.load((workflows / "build.yml").read_text(encoding="utf-8"))
    steps = publish["jobs"]["publish"]["steps"]
    setup_index = next(
        i for i, step in enumerate(steps) if step.get("uses", "").startswith("astral-sh/setup-uv@")
    )
    uvx_indices = [i for i, step in enumerate(steps) if "uvx" in step.get("run", "").split()]
    assert uvx_indices
    assert all(setup_index < i for i in uvx_indices)
    setup = steps[setup_index]
    assert setup["with"]["python-version"] == "3.12"
    for job in build["jobs"].values():
        build_setup = next(
            step for step in job["steps"] if step.get("uses", "").startswith("astral-sh/setup-uv@")
        )
        assert setup["uses"] == build_setup["uses"]
        assert setup["with"]["version"] == build_setup["with"]["version"]


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
    project = release.tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    version = project["version"]
    wheel_distribution = release.re.sub(r"[-_.]+", "_", project["name"]).lower()
    names = [
        f"{wheel_distribution}-{version}-py3-none-any.whl",
        f"{wheel_distribution}-{version}.tar.gz",
        "kural-windows-x64.zip",
        "kural-windows-x64-setup.exe",
    ]
    with pytest.raises(ValueError):
        release.checksums(tmp_path, version)
    for name in names:
        (tmp_path / name).write_bytes(b"verified artifact")
    release.checksums(tmp_path, version)
    assert len((tmp_path / "SHA256SUMS").read_text().splitlines()) == 4
    (tmp_path / "SHA256SUMS").unlink()
    (tmp_path / names[0]).write_bytes(b"")
    with pytest.raises(ValueError, match="Empty"):
        release.checksums(tmp_path, version)


def test_artifact_check_accepts_normalized_wheel_and_sdist_names(tmp_path):
    project = release.tomllib.loads(
        (Path(__file__).parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    )["project"]
    version = project["version"]
    distribution = release.re.sub(r"[-_.]+", "_", project["name"]).lower()
    names = [
        f"{distribution}-{version}-py3-none-any.whl",
        f"{distribution}-{version}.tar.gz",
        "kural-windows-x64.zip",
        "kural-windows-x64-setup.exe",
    ]
    for name in names:
        (tmp_path / name).write_bytes(b"verified artifact")

    release.checksums(tmp_path, version)
    assert len((tmp_path / "SHA256SUMS").read_text().splitlines()) == 4

    (tmp_path / "SHA256SUMS").unlink()
    (tmp_path / names[0]).rename(tmp_path / f"{project['name']}-{version}-py3-none-any.whl")
    with pytest.raises(ValueError, match="artifact set"):
        release.checksums(tmp_path, version)


def test_artifact_check_rejects_version_mismatch(tmp_path):
    with pytest.raises(ValueError, match="does not match pyproject.toml"):
        release.checksums(tmp_path, "0.1.0")


def test_artifact_check_rejects_unbumped_release_version(tmp_path):
    with pytest.raises(ValueError, match="does not match pyproject.toml"):
        release.checksums(tmp_path, "0.1.1")
