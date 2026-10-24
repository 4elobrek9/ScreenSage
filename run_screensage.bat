@echo off
rem ============================================================
rem  Self-relaunch in a hidden window, then run normally.
rem  If something fails (no PowerShell) - fall back to visible run.
rem ============================================================
if /i "%~1"=="hidden" goto :run

set "SELF=%~f0"
where powershell >nul 2>nul
if errorlevel 1 goto :run

powershell -NoProfile -WindowStyle Hidden -Command "Start-Process -FilePath cmd.exe -ArgumentList '/c', $env:SELF, 'hidden' -WindowStyle Hidden" >nul 2>nul
exit /b 0

rem ============================================================
rem  Normal (hidden) run
rem ============================================================
:run
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher not found. Install Python 3.11 or newer and enable the "py" launcher.
    exit /b 1
)

py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>nul
if errorlevel 1 (
    echo Python 3.11 or newer is required. Install it from https://www.python.org/downloads/windows/
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment...
    py -3 -m venv .venv
    if errorlevel 1 (
        echo Failed to create the virtual environment.
        exit /b 1
    )
)

".venv\Scripts\python.exe" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('screensage') else 1)" >nul 2>nul
if errorlevel 1 (
    echo Installing ScreenSage and its dependencies...
    ".venv\Scripts\python.exe" -m pip install -e .
    if errorlevel 1 (
        echo Installation failed. Check your internet connection and Python installation.
        exit /b 1
    )
)

echo Starting ScreenSage...
".venv\Scripts\python.exe" -m screensage
exit /b %ERRORLEVEL%