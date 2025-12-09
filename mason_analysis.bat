@echo off
REM mason_analysis.bat - Mason Reversal Analysis Pipeline
REM Double-click this file to launch the interactive analysis tool
REM
REM Usage:
REM   mason_analysis.bat          Run interactive analysis
REM   mason_analysis.bat check    Check environment requirements
REM   mason_analysis.bat install  Install Python dependencies

REM Get the directory where this batch file is located
set "PIPELINE_ROOT=%~dp0"
pushd "%PIPELINE_ROOT%"

REM Set Python path to include the pipeline
set "PYTHONPATH=%PIPELINE_ROOT%;%PYTHONPATH%"

echo ============================================================
echo   Mason Reversal Analysis Pipeline
echo ============================================================
echo.

REM Check for command-line arguments
if "%1"=="check" (
    python mason_cli.py check
    goto :end
)

if "%1"=="install" (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
    echo Checking Quarto...
    where quarto >nul 2>&1
    if errorlevel 1 (
        echo Quarto not found. Installing via winget...
        winget install Posit.Quarto --accept-source-agreements --accept-package-agreements
    ) else (
        echo Quarto already installed.
    )
    goto :end
)

if "%1"=="help" (
    echo Usage:
    echo   mason_analysis.bat          Run interactive analysis
    echo   mason_analysis.bat check    Check environment requirements
    echo   mason_analysis.bat install  Install Python dependencies
    echo   mason_analysis.bat help     Show this help
    goto :end
)

REM Run the interactive CLI
python mason_cli.py

:end
REM Keep window open so user can see results
echo.
echo Press any key to close...
pause >nul

popd

