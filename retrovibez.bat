@echo off
REM retrovibez.bat - RetroVibez Larval Reversal Detection Pipeline
REM Double-click this file to launch the interactive analysis tool
REM
REM Usage:
REM   retrovibez.bat          Run interactive analysis
REM   retrovibez.bat check    Check environment requirements
REM   retrovibez.bat install  Install Python dependencies

REM Get the directory where this batch file is located
set "PIPELINE_ROOT=%~dp0"
pushd "%PIPELINE_ROOT%"

REM Set Python path to include the pipeline
set "PYTHONPATH=%PIPELINE_ROOT%;%PYTHONPATH%"

echo ============================================================
echo   RetroVibez - Larval Reversal Detection Pipeline
echo ============================================================
echo.

REM Check for command-line arguments
if "%1"=="check" (
    python retrovibez_cli.py check
    goto :end
)

if "%1"=="install" (
    echo ============================================================
    echo   Installing RetroVibez Dependencies
    echo ============================================================
    echo.
    echo [1/5] Python packages...
    pip install -r requirements.txt
    echo.
    echo [2/5] Checking Quarto...
    where quarto >nul 2>&1
    if errorlevel 1 (
        echo Quarto not found. Installing via winget...
        winget install Posit.Quarto --accept-source-agreements --accept-package-agreements
    ) else (
        echo Quarto already installed.
    )
    echo.
    echo [3/5] Installing TinyTeX for PDF rendering...
    quarto install tinytex --update-path
    echo.
    echo [4/5] Checking MATLAB Engine for Python...
    python -c "import matlab.engine" 2>nul
    if errorlevel 1 (
        echo.
        echo MATLAB Engine not found. Install manually:
        echo   cd "C:\Program Files\MATLAB\R2024a\extern\engines\python"
        echo   python -m pip install .
        echo.
    ) else (
        echo MATLAB Engine already installed.
    )
    echo.
    echo [5/5] Verifying installation...
    python retrovibez_cli.py check
    echo.
    echo Installation complete!
    goto :end
)

if "%1"=="help" (
    echo Usage:
    echo   retrovibez.bat          Run interactive analysis
    echo   retrovibez.bat check    Check environment requirements
    echo   retrovibez.bat install  Install Python dependencies
    echo   retrovibez.bat help     Show this help
    goto :end
)

REM Run the interactive CLI
python retrovibez_cli.py

:end
REM Keep window open so user can see results
echo.
echo Press any key to close...
pause >nul

popd

