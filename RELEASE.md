# Release Guide for Kural

This document outlines the maintainer procedures for releasing Kural desktop assets and Python distributions. The existing v0.1.0 GitHub Release uses distribution `kural`; because that PyPI name belongs to an unrelated project, the next Python distribution is `cmd-kural` version 0.1.2. Attempted version 0.1.1 was not published: its Git tag points to a pre-fix commit, and release validation correctly requires the tag commit to be on current main. Desktop installer/ZIP releases remain on GitHub Releases. The 0.1.2 wheel/sdist build and isolated `uv tool` smoke tests pass locally, but a real install exposed stale version reporting (`kural --version` prints 0.1.0-dev while distribution metadata is 0.1.2). A code/version fix is being prepared as 0.1.3; no PyPI upload has occurred.

---

## 1. Overview & Release Architecture

Kural uses automated GitHub Actions workflows to validate, package, and publish releases:

1. **Tag Push (`v*.*.*`):** Triggers `.github/workflows/release.yml`.
2. **Validation Job (`validate`):**
   - Validates that the git tag strictly matches `vX.Y.Z` semantic version format.
   - Asserts that the tag matches `version` in `pyproject.toml` (e.g. `v0.1.0` requires `version = "0.1.0"`).
   - Validates that the tag commit is an ancestor of `origin/main` (preventing accidental releases from detached or unmerged branches).
3. **Build Pipeline (`build.yml`):**
   - Runs `ruff check .` and `ruff format --check .`.
   - Executes all 579 unit tests offline (`pytest -m "not gpu and not mic"`).
   - Builds Python distribution packages (`uv build --out-dir dist/packages`).
   - Runs `twine check --strict` on built packages.
   - Runs isolated `uv tool install` smoke tests outside the repository.
   - Compiles standalone Windows executable with PyInstaller (`packaging/kural.spec`).
   - Archives portable bundle (`kural-windows-x64.zip`).
   - Compiles Windows setup wizard installer with Inno Setup 6 (`packaging/kural.iss`).
   - Runs smoke tests for both the portable bundle and the setup installer.
4. **Publishing Job (`github-release`):**
   - Generates cryptographically verified `SHA256SUMS`.
   - Creates a GitHub Release for the tag with auto-generated release notes.
   - Attaches all 5 downloadable assets:
     - `kural-windows-x64-setup.exe` (Windows Installer)
     - `kural-windows-x64.zip` (Portable ZIP Bundle)
     - `kural-X.Y.Z-py3-none-any.whl` (Python Wheel)
     - `kural-X.Y.Z.tar.gz` (Source Distribution)
     - `SHA256SUMS` (Checksums manifest)
5. **Separate optional PyPI publication (`publish-pypi.yml`):**
   - Publishes the Python distribution named `cmd-kural` (the import package and CLI remain `kural`).
   - Requires the repository variable `PUBLISH_PYPI=true`, the protected GitHub Environment `pypi`, and a matching PyPI Trusted Publisher.
   - Uses OIDC without long-lived API tokens. It is a manual, tag-validating workflow separate from the GitHub Release workflow.
   - v0.1.0 remains the original GitHub Release with distribution name `kural`. PyPI uses `cmd-kural`; v0.1.2 is published but reports stale CLI/module versions, so prepare and verify 0.1.3 before directing users to PyPI. The failed v0.1.1 tag remains untouched.

---

## 2. Pre-Release Checklist

Before tagging a release, ensure:

- [ ] All feature and bug-fix PRs for the milestone are merged into `main`.
- [ ] Working tree is clean: `git status` shows nothing to commit.
- [ ] Version in `pyproject.toml` is up to date:
  ```toml
  [project]
  version = "0.1.0"
  ```
- [ ] `CHANGELOG.md` has an entry for the release version with all notable changes.
- [ ] Local tests and linting pass:
  ```powershell
  uv run ruff check .
  uv run ruff format --check .
  uv run pytest -m "not gpu and not mic"
  ```
- [ ] The latest commit on `main` has a green checkmark in GitHub Actions.
- [ ] Install the exact wheel/sdist from `dist/packages` into an isolated uv tool environment; verify `kural --version` and `kural.__version__` match the `cmd-kural` distribution metadata version.

---

## 3. Creating and Publishing a Release

### Step 1: Ensure Local `main` Is Up to Date

```powershell
git checkout main
git pull origin main
```

### Step 2: Create an Annotated Git Tag

Tags must strictly follow the `vX.Y.Z` format matching `pyproject.toml`:

```powershell
# For version 0.1.0:
git tag -a v0.1.0 -m "Release v0.1.0: Local-first voice typing and voice control for Windows"
```

### Step 3: Push the Tag to GitHub

Pushing the tag initiates the automated release workflow:

```powershell
git push origin v0.1.0
```

### Step 4: Monitor the Release Workflow

Watch the release run in GitHub Actions:

```powershell
gh run list --workflow=release.yml
gh run watch <run-id>
```

Alternatively, visit:
`https://github.com/mdaashir/kural/actions/workflows/release.yml`

---

## 4. Manual Release Dispatch (Alternative)

If you prefer triggering a release manually via the GitHub CLI or web UI:

```powershell
gh workflow run release.yml -f tag=v0.1.0
```

The workflow will validate that `v0.1.0` exists, points to an ancestor of `main`, and matches `pyproject.toml`.

---

## 5. Post-Release Verification

### Step 1: Verify the GitHub Release Page

Visit: `https://github.com/mdaashir/kural/releases/tag/v0.1.0`

Verify that all 5 assets are present:
1. `kural-windows-x64-setup.exe`
2. `kural-windows-x64.zip`
3. `kural-0.1.0-py3-none-any.whl`
4. `kural-0.1.0.tar.gz`
5. `SHA256SUMS`

### Step 2: Verify Checksums

Download the release assets into a temporary directory and verify checksums:

```powershell
gh release download v0.1.0 --dir dist-verify
cd dist-verify
Get-FileHash -Algorithm SHA256 *
Get-Content SHA256SUMS
```

### Step 3: Test Installation on Windows

Test the downloaded Windows setup installer:
1. Run `kural-windows-x64-setup.exe`.
2. Follow the setup wizard (installs to `%LOCALAPPDATA%\Programs\Kural`).
3. Launch `kural --version` and `kural --doctor`.

Or test `uv tool` installation from the wheel:
```powershell
uv tool install --force .\kural-0.1.0-py3-none-any.whl
kural --version
```

---

## 6. PyPI Trusted Publisher Setup (Optional; `cmd-kural`)

**Publication is pending.** Approved run `44851392430` failed metadata validation with `uvx: command not found` (exit 127), before upload. The fix installs pinned uv and Python 3.12 in the isolated publish job. The existing `v0.1.2` GitHub Release/tag remains unchanged. After this fix is reviewed and merged, an owner-authorized fresh dispatch from `main` can use that same tag; rerunning the old workflow would retain the missing setup. No dispatch or deployment approval is part of this fix. The existing PyPI project named `kural` belongs to an unrelated package. The v0.1.0 GitHub Release remains unchanged. Attempted v0.1.1 was not published because its tag points before the artifact-normalization fix; leave tag `v0.1.1` unchanged. This setup is for `cmd-kural` 0.1.2.

### Step 1: Configure a Pending Publisher for a New Project

Sign in to the intended owning PyPI account and use account **Publishing** to add a pending publisher for `cmd-kural`. It creates the project on the first successful upload; an existing project is not required. A pending publisher does not reserve the name. If another owner takes it, stop rather than upload to an unrelated project.

### Step 2: Verify the PyPI Trusted Publisher

For an existing project you own, use its **Publishing** settings; for a new project, verify the pending publisher from Step 1. Choose **GitHub** with exactly:

| PyPI field | Value |
|---|---|
| PyPI Project Name | `cmd-kural` |
| Owner | `mdaashir` |
| Repository name | `kural` |
| Workflow name | `publish-pypi.yml` |
| Environment name | `pypi` |

Do not create an API token. The workflow uses GitHub OIDC (`id-token: write`) and the `pypa/gh-action-pypi-publish` trusted-publisher action.

### Step 3: Configure the Protected GitHub Environment

In repository **Settings → Environments → New environment**, create an environment named exactly `pypi`. Add protection rules; recommended: required reviewer(s) and deployment-branch/tag restrictions for release refs. The PyPI publisher's environment value must match this name exactly.

### Step 4: Keep Publishing Disabled Until Ready

The workflow gate is the repository Actions variable:

- Name: `PUBLISH_PYPI`
- Value: `true`

Leave it unset (or set to any other value) until version 0.1.3 is merged and all account/publisher setup is complete. Version 0.1.2 is already published; its CLI/module version-reporting defect is being fixed for 0.1.3. Do not retry publishing 0.1.2. The manual workflow validates that the supplied existing tag matches `pyproject.toml` and points to a commit on `main`. The failed v0.1.1 tag also points to a pre-fix commit; do not move, force-update, or retry it.

### Step 5: First PyPI Publication

After the 0.1.3 version-fix PR is reviewed and merged:

1. Confirm `pyproject.toml` and `uv.lock` specify `cmd-kural` version `0.1.3` and changelog/docs match.
2. Create and push a new annotated `v0.1.3` tag from current `main`; do not move `v0.1.1` or `v0.1.2`.
3. Verify the `v0.1.3` GitHub Release workflow completed and artifacts/checksums are valid.
4. Verify the pending (or existing project) Trusted Publisher with the exact fields above and protected GitHub environment `pypi`.
5. Verify repository variable `PUBLISH_PYPI=true` and explicit owner authorization before proceeding.
6. Trigger a fresh publisher run from merged `main` for the new tag:

```powershell
gh workflow run publish-pypi.yml -f tag=v0.1.3
```

Approve the protected `pypi` environment if prompted. Watch the workflow and verify `https://pypi.org/project/cmd-kural/0.1.3/`. Install and check the published CLI version:

```powershell
uv tool install --python 3.12 --from "cmd-kural[runtime,tray]==0.1.3" kural
kural --version  # must report kural 0.1.3
```

The PyPI distribution is `cmd-kural`; its import package and console command remain `kural`. This job publishes only the Python wheel and source archive; it does not publish to GitHub Packages, create a GitHub Release, or deploy the website. The GitHub Release workflow remains separate.

If PyPI reports that the name is owned by another account or the trusted publisher does not match, stop and keep `PUBLISH_PYPI` disabled. Do not attempt to publish the existing `kural` name.

---

## 7. Container Images (GHCR & Docker Hub)

Kural's headless Whisper API server is packaged as an OCI container image via `.github/workflows/docker.yml`.

1. **GitHub Container Registry (GHCR):**
   - Automatically published to `ghcr.io/mdaashir/kural` on every push to `main` and version tag (`v*`).
   - Includes OCI annotation `LABEL org.opencontainers.image.source` linking the container directly to the repository's **Packages** sidebar.

2. **Docker Hub (Optional):**
   - If `DOCKERHUB_TOKEN` secret (or `DOCKERHUB_OIDC_CONNECTIONID` variable) and `DOCKERHUB_USERNAME` variable are configured in GitHub Actions, the workflow automatically authenticates and publishes dual tags to `docker.io/<username>/kural`.
   - If not configured, Docker Hub publishing is skipped safely without failing the workflow.

---

## 8. Rollback Procedures

If a critical issue is discovered post-release:

1. **Delete the GitHub Release & Tag:**
   ```powershell
   gh release delete v0.1.0 --yes
   git push --delete origin v0.1.0
   git tag -d v0.1.0
   ```
2. **Publish a Patch Release (`v0.1.3`, if `v0.1.2` is current):**
   - Fix the issue on a branch following the `AGENTS.md` workflow.
   - Bump version in `pyproject.toml` to the next unused patch version.
   - Update `CHANGELOG.md` and `uv.lock`.
   - Create and push a new annotated version tag; never move or force-update an existing release tag.
