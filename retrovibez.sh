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
        echo "[1/4] Python packages..."
        pip3 install -r requirements.txt
        echo
        echo "[2/4] Checking Quarto..."
        if ! command -v quarto &> /dev/null; then
            echo "Quarto not found. Install from: https://quarto.org/docs/download/"
            echo "  Mac: brew install quarto"
            echo "  Linux: Download .deb/.rpm from quarto.org"
        else
            echo "Quarto installed: $(quarto --version)"
        fi
        echo
        echo "[3/4] Installing TinyTeX for PDF rendering..."
        quarto install tinytex --update-path
        echo
        echo "[4/4] Verifying installation..."
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

