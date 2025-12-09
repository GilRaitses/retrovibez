#!/usr/bin/env python3
"""
RetroVibez Launcher
Cross-platform entry point - auto-detects OS and runs appropriate script.

Usage:
    python launch.py              Run analysis
    python launch.py install      Install dependencies
    python launch.py check        Check requirements
"""

import sys
import os
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def main():
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    
    if sys.platform == 'win32':
        # Windows - run .bat
        script = SCRIPT_DIR / 'retrovibez.bat'
        cmd = ['cmd', '/c', str(script)] + args
    else:
        # macOS / Linux - run .sh
        script = SCRIPT_DIR / 'retrovibez.sh'
        # Ensure executable
        os.chmod(script, 0o755)
        cmd = [str(script)] + args
    
    try:
        result = subprocess.run(cmd, cwd=SCRIPT_DIR)
        return result.returncode
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

