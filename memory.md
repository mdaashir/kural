# Memory — Windows Desktop Launcher UX

Last updated: 2026-11-21

## Current state
- `cmd-kural==0.1.3` is published on PyPI; GitHub Release v0.1.3 assets and checksums verified.
- PR #103 merged: headless API image published to GHCR. PR #104 merged: Next.js site deployed at https://mdaashir.github.io/kural/.
- Branch `feat/windowed-desktop-launcher` contains uncommitted launcher work for PR #106.
- Installed v0.1.3 log confirms CUDA/cuDNN DLL initialization failure. Installer does not bundle NVIDIA inference libraries; whisper model downloads on first use.

## Current change scope
- Separate PyInstaller `kural.exe` windowed GUI and `kural-console.exe` CLI via filename-selecting entrypoint.
- Inno Setup creates Start Menu shortcut and optional (default-selected) desktop shortcut to GUI.
- GUI CLI actions forward to visible console executable.
- Windowed stdout/stderr discarded to avoid a console; logging remains configured to user log. Startup exceptions attempt a native error dialog directing users to console doctor/log.
- Active-session model errors show in overlay and log; device selection is never silently changed.

## Verified
- Ruff clean; full pytest 599 passed.
- Local PyInstaller build created both executables. Console `--version` and `--packaging-smoke` passed. Windowed executable was not launched to avoid first-run model download.
- Inno Setup installer compilation/installation and hosted CI remain to verify.

## Known issue / next decision
- WhisperEngine constructor still raises when initial CUDA/cuDNN probing fails, before `KuralRuntime.run()` and tray startup. The windowed wrapper can log and show a message box, but it cannot keep the tray/settings alive after constructor failure. Do not claim startup recovery is fixed.
- Separate follow-up: design explicit CUDA setup vs CPU mode onboarding without silently changing user config or downloading large models without consent.
- App icon/signing is also follow-up; installer is unsigned.

## Project rules
- Follow `AGENTS.md`: feature branches, focused PRs, run checks, update SESSION on each iteration, wait for review/merge.
- Never create or push release tags without explicit authorization.
