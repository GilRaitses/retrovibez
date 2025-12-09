@echo off
REM ============================================================
REM   RETROVIBEZ - Double-click to launch
REM ============================================================
REM This is the only file you need to run.
REM It checks requirements and starts the analysis pipeline.

cd /d "%~dp0"

echo.
echo  ====================================================
echo   RETROVIBEZ - Larval Reversal Detection Pipeline
echo  ====================================================
echo.

REM Check if Python exists
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo.
    echo Install Python 3.8+ from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

REM Run system check and then CLI
python retrovibez_cli.py

echo.
pause

