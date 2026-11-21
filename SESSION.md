# SESSION.md

## Current milestone
**Windows desktop UX: separate windowed launcher and visible console CLI**

## Current branch
`fix/windows-app-launcher-and-shortcuts`

## PR
To be opened after final verification.

## Confirmed installed-app diagnosis
- Installer shortcut launched a PyInstaller executable built with `console=True`, so double-clicking opened a terminal.
- Inno Setup created no desktop shortcut, and the bundle initially exposed one `kural.exe`.
- Installed Kural log reports model initialization failure because NVIDIA cuBLAS/cuDNN DLLs are absent. The installer does not bundle these libraries; the model is downloaded on first use.
- Upstream `drajb/whisper-local` uses a bootstrap single-file executable, but that does not solve Kural's CUDA DLL issue. Preserve Kural's own packaging and explicitly document first-run requirements.

## This PR scope
- Separate windowed `kural.exe` and console `kural-console.exe` PyInstaller launchers sharing one parser/runtime.
- Inno Setup Start Menu shortcut plus optional desktop shortcut (checked by default) targets the windowed launcher.
- CLI/diagnostic options invoked from the frozen windowed executable are forwarded to sibling `kural-console.exe`.
- Model-load errors during an active transcription are surfaced in the overlay and log instead of being misreported as no speech.
- No automatic CPU switch, CUDA package installation, configuration mutation, model download, or user-profile modification.

## Verification
- Ruff check and format passed (144 files).
- Focused runtime/model tests: 58 passed.
- Full test suite: 599 passed; retry-last regression uses an immediate fake thread to avoid async teardown races.
- Local PyInstaller bundle build created both executables; console `--version` and `--packaging-smoke` passed.
- Fresh portable ZIP smoke passed; it inspected the GUI executable but did not launch it.

## Next steps
1. Verify installer compilation and hosted Windows packaging smoke in the PR.
2. Wait for review and merge.
3. Handle first-start recovery for missing CUDA/cuDNN in a separate PR; add branded app icon/installer artwork separately.

## Limitations
- Initial CUDA failure still aborts runtime construction before tray startup; this PR does not make the app usable after that failure.
- CUDA/cuDNN libraries remain external prerequisites for GPU inference and are not installed by the app. The user's configured device was not changed.
- The installed app was not relaunched after diagnosis; the GUI executable was not started during verification.
- The installer is unsigned; SmartScreen and app signing are separate work.
