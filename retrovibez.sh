#!/bin/bash
# retrovibez.sh - RetroVibez Larval Reversal Detection Pipeline
# Linux/Mac launcher
#
# Usage:
#   ./retrovibez.sh          Run interactive analysis
#   ./retrovibez.sh check    Check environment requirements
#   ./retrovibez.sh install  Install Python dependencies

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

echo "============================================================"
echo "  RetroVibez - Larval Reversal Detection Pipeline"
echo "============================================================"
echo

case "$1" in
    check)
        python3 retrovibez_cli.py check
        ;;
    install)
        echo "============================================================"
        echo "  Installing RetroVibez Dependencies"
        echo "============================================================"
        echo
        echo "[1/5] Python packages..."
        pip3 install -r requirements.txt
        echo
        echo "[2/5] Checking Quarto..."
        if ! command -v quarto &> /dev/null; then
            echo "Quarto not found. Install from: https://quarto.org/docs/download/"
            echo "  Mac: brew install quarto"
            echo "  Linux: Download .deb/.rpm from quarto.org"
        else
            echo "Quarto installed: $(quarto --version)"
        fi
        echo
        echo "[3/5] Installing TinyTeX for PDF rendering..."
        quarto install tinytex --update-path
        echo
        echo "[4/5] Checking MATLAB Engine for Python..."
        if python3 -c "import matlab.engine" 2>/dev/null; then
            echo "MATLAB Engine already installed."
        else
            echo
            echo "MATLAB Engine not found. Install manually:"
            echo "  Mac:   cd /Applications/MATLAB_R2024a.app/extern/engines/python && pip3 install ."
            echo "  Linux: cd /usr/local/MATLAB/R2024a/extern/engines/python && sudo pip3 install ."
            echo
        fi
        echo
        echo "[5/5] Verifying installation..."
        python3 retrovibez_cli.py check
        echo
        echo "Installation complete!"
        ;;
    help|--help|-h)
        echo "Usage:"
        echo "  ./retrovibez.sh          Run interactive analysis"
        echo "  ./retrovibez.sh check    Check environment requirements"
        echo "  ./retrovibez.sh install  Install Python dependencies"
        echo "  ./retrovibez.sh help     Show this help"
        ;;
    *)
        python3 retrovibez_cli.py
        ;;
esac

echo
echo "Press Enter to close..."
read

