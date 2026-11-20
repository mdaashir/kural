@echo off
setlocal
cd /d "%~dp0\.."

uv sync --locked --python 3.12 --extra dev --extra runtime --extra tray
if errorlevel 1 exit /b 1
uv run --no-sync pyinstaller --noconfirm --clean packaging\kural.spec
if errorlevel 1 exit /b 1
powershell -NoProfile -Command "Compress-Archive -Path dist\kural\* -DestinationPath dist\kural-windows-x64.zip -Force"
if errorlevel 1 exit /b 1
uv run --no-sync python packaging\smoke.py --bundle dist\kural-windows-x64.zip
if errorlevel 1 exit /b 1
echo Verified standalone archive: dist\kural-windows-x64.zip
