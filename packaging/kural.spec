# PyInstaller spec for Kural (Windows standalone executable).
#
#   packaging\build.bat                               (creates build venv and packages)
#   pyinstaller --noconfirm packaging\kural.spec     (from the repo root)
#
# Output: dist\kural\kural.exe plus dependencies.
import os
from pathlib import Path

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))  # noqa: F821
KURAL = os.path.join(ROOT, "kural")

datas = [
    (os.path.join(KURAL, "config", "config.defaults.yaml"), "kural/config"),
    (os.path.join(KURAL, "config", "commands.defaults.yaml"), "kural/config"),
    (os.path.join(KURAL, "config", "app_rules.defaults.yaml"), "kural/config"),
    (os.path.join(ROOT, "pyproject.toml"), "."),
]

hiddenimports = [
    "kural",
    "kural.config",
    "kural.control",
    "kural.engine",
    "kural.ui",
    "kural.doctor",
    "kural.selftest",
    "ruamel.yaml",
    "pyperclip",
]

# Optional dynamic libraries and packages if present in build environment
binaries = []
try:
    from PyInstaller.utils.hooks import collect_data_files, collect_dynamic_libs
    binaries += collect_dynamic_libs("ctranslate2")
    datas += collect_data_files("faster_whisper")
except Exception:
    pass

a = Analysis(  # noqa: F821
    [os.path.join(KURAL, "__main__.py")],  # noqa: F821
    pathex=[ROOT],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=[
        "pytest",
        "ruff",
        "IPython",
        "matplotlib",
        "tkinter.test",
        "unittest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="kural",
    console=True,  # console enabled for CLI diagnostics and --doctor
    upx=False,     # avoid antivirus heuristics
    disable_windowed_traceback=False,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="kural",
)
