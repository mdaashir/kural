@echo off
setlocal enabledelayedexpansion

echo =======================================================
echo Building Kural Windows Standalone Distribution
echo =======================================================

cd /d "%~dp0\.."

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found at .venv. Please run: uv venv
    exit /b 1
)

echo [1/3] Ensuring build dependencies are installed...
.venv\Scripts\python.exe -m pip install --quiet pyinstaller "ruamel.yaml>=0.18.0"

echo [2/3] Running PyInstaller...
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean packaging\kural.spec
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

echo [3/3] Build succeeded!
echo Standalone binary is available at: dist\kural\kural.exe
echo Run 'dist\kural\kural.exe --doctor' to verify installation.

exit /b 0
