#!/bin/bash
# ============================================================
#   RETROVIBEZ - Launch script (Linux)
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
    echo "Install Python 3.8+: sudo apt install python3"
    echo
    exit 1
fi

# Run
python3 retrovibez_cli.py

