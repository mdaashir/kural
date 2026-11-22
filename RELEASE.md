# Release Guide for Kural

This document outlines maintainer procedures for releasing Kural desktop assets and Python distributions. GitHub Release v0.1.3 publishes the Windows installer, portable ZIP, Python wheel/sdist, and SHA256SUMS. PyPI `cmd-kural` v0.1.3 is also published. Its CLI currently reports stale module metadata (`kural 0.1.0`); the correction is prepared for v0.1.4 in a pending PR. The Windows installer uses windowed GUI and console CLI executables; CUDA/cuDNN inference libraries are not bundled.

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
   - Executes the offline unit suite (`pytest -m "not gpu and not mic"`); use the linked CI run for the current count.
   - Builds Python distribution packages (`uv build --out-dir dist/packages`).
   - Runs `twine check --strict` on built packages.
   - Runs isolated `uv tool install` smoke tests outside the repository.
   - Compiles separate `kural-console.exe` (CLI) and `kural.exe` (windowed GUI) launchers with PyInstaller (`packaging/kural.spec`).
   - Archives both launchers and runtime dependencies in `kural-windows-x64.zip`.
   - Compiles Windows setup wizard installer with Inno Setup 6 (`packaging/kural.iss`), with Start Menu and optional desktop shortcuts targeting the windowed app.
   - Runs smoke tests for CLI diagnostics, portable-bundle contents, and setup install/uninstall without starting the windowed app or downloading a model.
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
   - GitHub Release `v0.1.3` provides the Windows installer, portable ZIP, Python wheel/sdist, and `SHA256SUMS` (see [GitHub Releases](https://github.com/mdaashir/kural/releases)). PyPI separately publishes `cmd-kural==0.1.3`; its import package and console command remain `kural`. Earlier failed tags `v0.1.1` and `v0.1.2` are immutable and must not be moved or retried.

---

## 2. Pre-Release Checklist

Before tagging a release, ensure:

- [ ] All feature and bug-fix PRs for the milestone are merged into `main`.
- [ ] Working tree is clean: `git status` shows nothing to commit.
- [ ] `pyproject.toml` and `uv.lock` agree on the new `cmd-kural` version (for example, `0.1.4`). Keep the Python distribution `cmd-kural` distinct from the import package and command `kural`.
- [ ] `CHANGELOG.md` has an entry for the release version with all notable changes.
- [ ] Local tests and linting pass:
  ```powershell
  uv run ruff check .
  uv run ruff format --check .
  uv run pytest -m "not gpu and not mic"
  ```
- [ ] The latest commit on `main` has a green checkmark in GitHub Actions.
- [ ] Build wheel and sdist; pass `twine check --strict`; install each into an isolated uv tool environment; verify `importlib.metadata.version('cmd-kural') == kural.__version__` and `kural --version` prints the same version.

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
# Replace X.Y.Z with the version in pyproject.toml, e.g. 0.1.4
git tag -a vX.Y.Z -m "Release vX.Y.Z: Local-first voice typing and voice control for Windows"
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
1. Run `kural-windows-x64-setup.exe`; select the optional desktop shortcut if desired.
2. Follow the setup wizard (installs to `%LOCALAPPDATA%\Programs\Kural`).
3. Launch the Start Menu or desktop shortcut. It targets the windowed `kural.exe`; terminal-based CLI diagnostics use `kural-console.exe --doctor` or `--version`.
4. On GPU systems run `kural-console.exe --doctor`. CUDA/cuDNN inference DLLs are not bundled in the installer. CUDA/cuDNN installation is not yet guided by the installer; until that flow is implemented, explicitly select CPU (`device: cpu`, `compute_type: int8`) in Settings/configuration if the required libraries are missing. Kural should not silently change the user's configured device or install CUDA dependencies in the background.

Or test `uv tool` installation from the wheel:
```powershell
uv tool install --force .\kural-0.1.0-py3-none-any.whl
kural --version
```

---

## 6. PyPI Trusted Publisher (`cmd-kural`)

`cmd-kural==0.1.3` was published to PyPI from GitHub Actions run `44860640871` after approval of the protected `pypi` environment. The GitHub Release v0.1.3 remains the source for desktop installer/ZIP assets; PyPI receives only the Python wheel and source archive. The older `kural` name belongs to an unrelated project. Failed tags v0.1.1 and v0.1.2 remain immutable and were not moved or retried.

The package and publisher were configured as follows; retain this configuration for future PyPI releases.

### Step 1: Configure the PyPI Project and Publisher (completed)

The owner configured a pending PyPI publisher for `cmd-kural`, which created the project on first successful upload. Pending publisher configuration does not reserve a name. If configuring a publisher for another new distribution, verify ownership before dispatching a publish.

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

### Step 4: Enable Publishing (completed)

The repository Actions variable `PUBLISH_PYPI=true`, protected `pypi` environment, and PyPI OIDC publisher are configured. The publish workflow requires manual dispatch and environment approval; it does not run automatically on GitHub Release tags.

### Step 5: Publish and Verify cmd-kural 0.1.3 (completed)

- GitHub Release `v0.1.3` was built and verified before the PyPI publish dispatch.
- The owner approved the `pypi` environment; GitHub Actions run `44860640871` uploaded the wheel and source archive through OIDC.
- PyPI reports `cmd-kural==0.1.3`; artifact hashes match the built release package files.
- A fresh `uv tool install --from "cmd-kural[runtime,tray]==0.1.3" kural` succeeded, but exposed a defect: distribution metadata is 0.1.3 while `kural.__version__` and `kural --version` reported 0.1.0. Do not direct users to install 0.1.3 expecting a corrected CLI version.

### Step 6: Correct CLI Version for the Next Release

The merged `main` fix changes installed version lookup to use `cmd-kural` metadata and source checkouts to report `0+unknown`. Prepare a new `cmd-kural` version `0.1.4` and a fresh GitHub tag/release; never move or reuse `v0.1.1`, `v0.1.2`, or `v0.1.3`. Verify the new wheel with isolated `uv tool install` and require `kural --version` and `kural.__version__` to report 0.1.4 before publishing. PyPI publishing uses:

```powershell
gh workflow run publish-pypi.yml -f tag=v0.1.4
```

Approve the protected environment when requested; then verify the uploaded artifacts at `https://pypi.org/project/cmd-kural/0.1.4/`. PyPI publishing uploads only the Python wheel/sdist; desktop artifacts remain on the GitHub Release, while GHCR and GitHub Pages are separate publishing/deployment workflows. Do not create or push release tags without explicit release authorization.

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
