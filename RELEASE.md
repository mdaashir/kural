# Release Guide for Kural

This document outlines the maintainer procedures for releasing a new version of Kural.

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
5. **Optional PyPI Publication (`pypi`):**
   - Gated behind the `PUBLISH_PYPI == 'true'` repository variable and the `pypi` GitHub Environment.
   - Uses PyPI Trusted Publishing (OIDC) without long-lived API tokens.

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

## 6. Enabling PyPI Publishing (Optional)

PyPI publishing is disabled by default for safety. To enable automatic PyPI publishing on release tags:

1. Register or claim the `kural` package name on [pypi.org](https://pypi.org).
2. Configure **Trusted Publishing (OIDC)** on PyPI:
   - Owner: `mdaashir`
   - Repository: `kural`
   - Workflow name: `release.yml`
   - Environment name: `pypi`
3. On GitHub (`Settings` → `Environments`), create the `pypi` environment with protection rules.
4. On GitHub (`Settings` → `Secrets and variables` → `Actions` → `Variables`), set:
   - Name: `PUBLISH_PYPI`
   - Value: `true`

---

## 7. Rollback Procedures

If a critical issue is discovered post-release:

1. **Delete the GitHub Release & Tag:**
   ```powershell
   gh release delete v0.1.0 --yes
   git push --delete origin v0.1.0
   git tag -d v0.1.0
   ```
2. **Publish a Patch Release (`v0.1.1`):**
   - Fix the issue on a branch following the `AGENTS.md` workflow.
   - Bump version in `pyproject.toml` to `0.1.1`.
   - Update `CHANGELOG.md`.
   - Tag and push `v0.1.1`.
