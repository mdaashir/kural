"""Tests for Docker containerization and GHCR packaging."""

from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).parents[1]


def test_dockerfile_structure():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    assert "FROM python:3.12-slim" in dockerfile
    assert "USER kural" in dockerfile
    assert "ENTRYPOINT" in dockerfile
    assert "EXPOSE 7777" in dockerfile
    assert "HEALTHCHECK" in dockerfile
    assert "uv pip install" in dockerfile
    assert ".[server]" in dockerfile
    assert "LABEL org.opencontainers.image.source" in dockerfile
    assert "https://github.com/mdaashir/kural" in dockerfile


def test_dockerignore_excludes_sensitive_paths():
    dockerignore = (ROOT / ".dockerignore").read_text(encoding="utf-8").splitlines()
    cleaned = [line.strip() for line in dockerignore if line.strip() and not line.startswith("#")]
    assert ".git" in cleaned
    assert ".venv" in cleaned
    assert ".pytest_cache" in cleaned


def test_docker_compose_loopback_binding():
    yaml = YAML(typ="safe")
    compose = yaml.load((ROOT / "docker-compose.yml").read_text(encoding="utf-8"))
    assert "services" in compose
    assert "kural-api" in compose["services"]
    ports = compose["services"]["kural-api"]["ports"]
    assert any("127.0.0.1" in str(p) for p in ports)


def test_docker_workflow_configuration():
    yaml = YAML(typ="safe")
    workflow = yaml.load(
        (ROOT / ".github" / "workflows" / "docker.yml").read_text(encoding="utf-8")
    )
    assert workflow["permissions"]["packages"] == "write"
    assert workflow["permissions"]["contents"] == "read"
    assert workflow["permissions"]["id-token"] == "write"
    steps = workflow["jobs"]["build"]["steps"]
    login_steps = [s for s in steps if "login-action" in s.get("uses", "")]
    assert any(s["with"]["registry"] == "ghcr.io" for s in login_steps)
    assert any(s["with"]["registry"] == "docker.io" for s in login_steps)
