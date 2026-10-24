@echo off
setlocal enabledelayedexpansion
title MONOLITH — Autonomous Engineering System
color 0B

:: Ensure working directory is the repository root
cd /d "%~dp0"

:: Force UTF-8 environment for Python on Windows
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

echo ====================================================================
echo   MONOLITH — Autonomous Engineering System
echo   "One system. Every intelligence. Total control."
echo   Local-First ^| Privacy-Governed Multi-Agent SDLC Platform
echo ====================================================================
echo.

:: Detect Python interpreter
set "PY_CMD="
if exist "%~dp0.venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0.venv\Scripts\python.exe"
) else if exist "%~dp0venv\Scripts\python.exe" (
    set "PY_CMD=%~dp0venv\Scripts\python.exe"
) else (
    where python >nul 2>&1
    if !errorlevel! equ 0 (
        set "PY_CMD=python"
    ) else (
        where py >nul 2>&1
        if !errorlevel! equ 0 (
            set "PY_CMD=py -3"
        ) else (
            echo [ERROR] Python 3.10+ was not found on your system PATH!
            echo Please install Python from https://www.python.org/downloads/
            pause
            exit /b 1
        )
    )
)

:: Direct launch flag check
if "%1"=="--direct" goto DIRECT_LAUNCH

:: Step 1: Open the Setup Wizard
echo [1/2] Launching MONOLITH Setup Wizard...
if exist "%~dp0setup_wizard.py" (
    !PY_CMD! "%~dp0setup_wizard.py"
    if !errorlevel! equ 0 (
        exit /b 0
    )
)

:DIRECT_LAUNCH
:: Step 2: Direct server start if wizard exited or --direct flag passed
echo [2/2] Starting MONOLITH on http://127.0.0.1:8001...
start "" "http://127.0.0.1:8001"
!PY_CMD! "%~dp0server.py"

echo.
echo MONOLITH has shut down.
pause
