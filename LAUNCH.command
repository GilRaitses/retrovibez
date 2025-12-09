#!/bin/bash
# ============================================================
#   RETROVIBEZ - Double-click to launch (macOS)
# ============================================================

cd "$(dirname "$0")"

echo
echo " ===================================================="
echo "  RETROVIBEZ - Larval Reversal Detection Pipeline"
echo " ===================================================="
echo

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python not found!"
    echo
    echo "Install Python 3.8+ from: https://www.python.org/downloads/"
    echo
    read -p "Press Enter to close..."
    exit 1
fi

# Run
python3 retrovibez_cli.py

echo
read -p "Press Enter to close..."

