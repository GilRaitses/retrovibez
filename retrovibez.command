#!/bin/bash
# retrovibez.command - RetroVibez for macOS
# Double-click this file in Finder to launch

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Run the main script
./retrovibez.sh "$@"

