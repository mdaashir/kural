"""Validate release identity and the complete downloadable artifact set."""

import argparse
import hashlib
import os
import re
import subprocess
import tomllib
from pathlib import Path


def validate_tag(tag: str) -> tuple[str, str]:
    """Resolve only an existing exact-version tag, never a branch or new tag."""
    if not re.fullmatch(r"v\d+\.\d+\.\d+", tag):
        raise ValueError("Expected an existing stable vX.Y.Z tag")
    commit = subprocess.check_output(
        ["git", "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}"], text=True
    ).strip()
    metadata = subprocess.check_output(["git", "show", f"{commit}:pyproject.toml"], text=True)
    version = tomllib.loads(metadata)["project"]["version"]
    if tag != f"v{version}":
        raise ValueError("Tag does not exactly match project version")
    subprocess.run(["git", "merge-base", "--is-ancestor", commit, "origin/main"], check=True)
    if os.environ.get("GITHUB_EVENT_NAME") == "push":
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        if head != commit:
            raise ValueError("Push checkout does not match the tag commit")
    return commit, version


def checksums(root: Path, version: str) -> None:
    """Reject missing, extra, empty or misversioned artifacts; write SHA256SUMS."""
    with (Path(__file__).parents[1] / "pyproject.toml").open("rb") as stream:
        project = tomllib.load(stream)["project"]
    wheel_distribution = re.sub(r"[-_.]+", "_", project["name"]).lower()
    if version != project["version"]:
        raise ValueError("Artifact version does not match pyproject.toml")
    expected = {
        f"{wheel_distribution}-{version}-py3-none-any.whl",
        f"{wheel_distribution}-{version}.tar.gz",
        "kural-windows-x64.zip",
        "kural-windows-x64-setup.exe",
    }
    files = [path for path in root.rglob("*") if path.is_file()]
    if len(files) != len(expected) or {p.name for p in files} != expected:
        raise ValueError("Release artifact set does not match expected names/version")
    lines = []
    for path in sorted(files, key=lambda p: p.name):
        if path.stat().st_size == 0:
            raise ValueError(f"Empty release artifact: {path.name}")
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}\n")
    (root / "SHA256SUMS").write_text("".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag")
    parser.add_argument("--artifacts", type=Path)
    parser.add_argument("--version")
    args = parser.parse_args()
    if args.tag:
        commit, version = validate_tag(args.tag)
        with Path(os.environ["GITHUB_OUTPUT"]).open("a", encoding="utf-8") as stream:
            stream.write(f"commit={commit}\nversion={version}\ntag={args.tag}\n")
    if args.artifacts:
        checksums(args.artifacts, args.version)


if __name__ == "__main__":
    main()
