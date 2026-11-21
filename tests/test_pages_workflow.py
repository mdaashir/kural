"""Static contract tests for GitHub Pages deployment configuration."""

from pathlib import Path

from ruamel.yaml import YAML

ROOT = Path(__file__).parents[1]


def test_pages_workflow_builds_pr_and_deploys_only_main():
    workflow = YAML(typ="safe").load(
        (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    )
    events = workflow["on"]
    assert events["pull_request"]["branches"] == ["main"]
    assert events["push"]["branches"] == ["main"]
    assert workflow["permissions"] == {"contents": "read"}
    build = workflow["jobs"]["build"]
    assert build["timeout-minutes"] == 15
    steps = build["steps"]
    commands = [step.get("run", "") for step in steps]
    assert "npm ci" in commands
    assert "npm run typecheck" in commands
    assert "npm run lint" in commands
    assert "npm run build" in commands
    assert "npm test" in commands
    upload = next(step for step in steps if "upload-pages-artifact" in step.get("uses", ""))
    assert upload["if"] == "github.event_name != 'pull_request' && github.ref == 'refs/heads/main'"
    assert upload["with"]["path"] == "site/out"
    deploy = workflow["jobs"]["deploy"]
    assert deploy["needs"] == "build"
    assert deploy["if"] == upload["if"]
    assert deploy["environment"]["name"] == "github-pages"
    assert deploy["permissions"] == {"pages": "write", "id-token": "write"}
