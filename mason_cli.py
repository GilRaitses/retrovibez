#!/usr/bin/env python3
"""
Mason Analysis Pipeline - Interactive CLI
Runs reversal detection, figure generation, and report rendering.
"""

import sys
import os
import re
from pathlib import Path
from datetime import datetime

# Add core module path
PIPELINE_ROOT = Path(__file__).parent
sys.path.insert(0, str(PIPELINE_ROOT))

from core.systemfairy import run_systemfairy, ensure_requirements
from core.matlab_runner import run_matlab_analysis
from core.figure_generator import generate_all_figures
from core.qmd_generator import generate_qmd_report
from core.report_renderer import render_report


def parse_track_selection(track_input: str, available_tracks: list = None) -> list:
    """
    Parse track selection string into list of track numbers.
    
    Supports:
        - 'all' -> all available tracks
        - '1,2,5' -> [1, 2, 5]
        - '1-10' -> [1, 2, 3, ..., 10]
        - '1,3,5-10,15' -> [1, 3, 5, 6, 7, 8, 9, 10, 15]
    """
    track_input = track_input.strip().lower()
    
    if track_input == 'all':
        return available_tracks if available_tracks else []
    
    tracks = set()
    parts = track_input.replace(' ', '').split(',')
    
    for part in parts:
        if '-' in part:
            # Range: 1-10
            match = re.match(r'(\d+)-(\d+)', part)
            if match:
                start, end = int(match.group(1)), int(match.group(2))
                tracks.update(range(start, end + 1))
        else:
            # Single number
            if part.isdigit():
                tracks.add(int(part))
    
    result = sorted(list(tracks))
    
    # Filter to available tracks if provided
    if available_tracks:
        result = [t for t in result if t in available_tracks]
    
    return result


def detect_data_type(path: Path):
    """
    Auto-detect the type of data at the given path.
    
    Returns:
        Tuple of (data_type, detected_path, available_tracks)
        - data_type: 'experiment', 'eset', 'collection', or 'unknown'
    """
    path = Path(path).resolve()
    
    if not path.exists():
        return 'unknown', None, []
    
    # Check if it's a .mat file (single experiment)
    if path.is_file() and path.suffix == '.mat':
        # Look for tracks directory
        tracks_pattern = path.parent.glob('*_*tracks')
        tracks_dir = next(tracks_pattern, None)
        available_tracks = []
        if tracks_dir:
            available_tracks = sorted([
                int(f.stem.replace('track', ''))
                for f in tracks_dir.glob('track*.mat')
            ])
        return 'experiment', path, available_tracks
    
    # It's a directory
    if path.is_dir():
        # Check for matfiles subdirectory (eset)
        matfiles = path / 'matfiles'
        if matfiles.exists():
            # Find experiment .mat files
            mat_files = list(matfiles.glob('*.mat'))
            if mat_files:
                # Single eset - look for tracks
                tracks_dirs = list(matfiles.glob('*tracks'))
                if tracks_dirs:
                    tracks_dir = tracks_dirs[0]
                    available_tracks = sorted([
                        int(f.stem.replace('track', ''))
                        for f in tracks_dir.glob('track*.mat')
                    ])
                    return 'eset', path, available_tracks
                return 'eset', path, []
        
        # Check for multiple eset directories (collection)
        eset_dirs = [d for d in path.iterdir() if d.is_dir() and (d / 'matfiles').exists()]
        if len(eset_dirs) > 1:
            return 'collection', path, []
        
        # Check if this is a matfiles directory directly
        if path.name == 'matfiles':
            return 'eset', path.parent, []
    
    return 'unknown', path, []


def discover_available_tracks(experiment_path: Path) -> list:
    """Find all available tracks for an experiment."""
    parent = experiment_path.parent if experiment_path.is_file() else experiment_path / 'matfiles'
    tracks_dirs = list(parent.glob('*tracks'))
    
    if not tracks_dirs:
        return []
    
    tracks_dir = tracks_dirs[0]
    return sorted([
        int(f.stem.replace('track', ''))
        for f in tracks_dir.glob('track*.mat')
    ])


def get_user_input():
    """Interactive prompts for path and track selection."""
    print("=" * 60)
    print("  Mason Reversal Analysis Pipeline")
    print("=" * 60)
    print()
    print("Drag a folder/file into this terminal and press Enter,")
    print("or type a path:")
    print()
    
    user_path = input("  Path: ").strip().strip('"').strip("'")
    
    if not user_path:
        print("\nNo path provided. Exiting.")
        return None, None, None
    
    path = Path(user_path)
    
    if not path.exists():
        print(f"\nPath does not exist: {path}")
        return None, None, None
    
    # Auto-detect data type
    data_type, detected_path, available_tracks = detect_data_type(path)
    
    print()
    print(f"Detected: {data_type}")
    print(f"Path: {detected_path}")
    
    if available_tracks:
        print(f"Available tracks: {len(available_tracks)} ({min(available_tracks)}-{max(available_tracks)})")
    
    # Track selection
    print()
    print("-" * 40)
    print("Track Selection Syntax:")
    print("  all       - All available tracks")
    print("  1,2,5     - Tracks 1, 2, and 5")
    print("  1-10      - Tracks 1 through 10")
    print("  1,3,5-10  - Tracks 1, 3, and 5-10")
    print("-" * 40)
    print()
    
    track_input = input("  Select tracks [all]: ").strip()
    
    if not track_input:
        track_input = 'all'
    
    selected_tracks = parse_track_selection(track_input, available_tracks)
    
    if not selected_tracks and available_tracks:
        print("\nNo valid tracks selected. Using all available tracks.")
        selected_tracks = available_tracks
    elif not selected_tracks:
        print("\nNo tracks found. Will process whatever is available.")
        selected_tracks = None  # Let MATLAB figure it out
    
    print()
    print(f"Selected tracks: {selected_tracks if selected_tracks else 'all available'}")
    
    # Output directory
    print()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    default_output = detected_path.parent / f"mason_results_{timestamp}"
    
    output_input = input(f"  Output directory [{default_output}]: ").strip().strip('"').strip("'")
    
    output_dir = Path(output_input) if output_input else default_output
    
    print()
    print("=" * 60)
    print("  Configuration Summary")
    print("=" * 60)
    print(f"  Data type: {data_type}")
    print(f"  Input: {detected_path}")
    print(f"  Tracks: {len(selected_tracks) if selected_tracks else 'all'}")
    print(f"  Output: {output_dir}")
    print("=" * 60)
    print()
    
    confirm = input("Proceed? [Y/n]: ").strip().lower()
    if confirm and confirm not in ('y', 'yes', ''):
        print("\nCancelled.")
        return None, None, None
    
    return detected_path, selected_tracks, output_dir


def run_pipeline(input_path: Path, tracks: list, output_dir: Path):
    """Execute the full analysis pipeline."""
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results_dir = output_dir / 'results'
    figures_dir = output_dir / 'figures'
    results_dir.mkdir(exist_ok=True)
    figures_dir.mkdir(exist_ok=True)
    
    print()
    print("=" * 60)
    print("  Step 1/4: MATLAB Analysis")
    print("=" * 60)
    
    success = run_matlab_analysis(
        input_path=input_path,
        tracks=tracks,
        output_dir=results_dir
    )
    
    if not success:
        print("\nMATLAB analysis failed. Aborting.")
        return False
    
    print()
    print("=" * 60)
    print("  Step 2/4: Figure Generation")
    print("=" * 60)
    
    generate_all_figures(
        results_dir=results_dir,
        figures_dir=figures_dir,
        tracks=tracks
    )
    
    print()
    print("=" * 60)
    print("  Step 3/4: QMD Report Generation")
    print("=" * 60)
    
    qmd_path = generate_qmd_report(
        results_dir=results_dir,
        figures_dir=figures_dir,
        output_dir=output_dir
    )
    
    print()
    print("=" * 60)
    print("  Step 4/4: Rendering PDF/HTML")
    print("=" * 60)
    
    render_report(qmd_path)
    
    print()
    print("=" * 60)
    print("  Pipeline Complete!")
    print("=" * 60)
    print()
    print(f"  Results:  {results_dir}")
    print(f"  Figures:  {figures_dir}")
    print(f"  Report:   {qmd_path.stem}.pdf / .html")
    print()
    
    return True


def main():
    """Main entry point."""
    # Check for special commands
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if cmd in ('check', 'systemfairy', '--check'):
            run_systemfairy(verbose=True)
            return 0
        elif cmd in ('install', '--install'):
            return install_dependencies()
        elif cmd in ('help', '--help', '-h'):
            print_help()
            return 0
    
    try:
        # Run environment check first
        print()
        ok, missing = run_systemfairy(verbose=True)
        
        if not ok:
            print()
            response = input("Continue anyway? [y/N]: ").strip().lower()
            if response not in ('y', 'yes'):
                return 1
        
        print()
        input_path, tracks, output_dir = get_user_input()
        
        if input_path is None:
            return 1
        
        success = run_pipeline(input_path, tracks, output_dir)
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\n\nInterrupted by user.")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


def install_dependencies():
    """Install Python dependencies non-interactively."""
    import subprocess
    
    print("Installing Python dependencies...")
    req_file = PIPELINE_ROOT / 'requirements.txt'
    
    result = subprocess.run(
        [sys.executable, '-m', 'pip', 'install', '-r', str(req_file)],
        capture_output=False
    )
    
    if result.returncode == 0:
        print("\nPython dependencies installed successfully.")
    else:
        print("\nFailed to install some dependencies.")
    
    return result.returncode


def print_help():
    """Print usage help."""
    print("""
Mason Analysis Pipeline
=======================

Usage:
  python mason_cli.py              Run interactive analysis
  python mason_cli.py check        Check environment requirements
  python mason_cli.py install      Install Python dependencies
  python mason_cli.py help         Show this help

Or double-click: mason_analysis.bat

Track Selection Syntax:
  all         All available tracks
  1,2,5       Tracks 1, 2, and 5
  1-10        Tracks 1 through 10
  1,3,5-10    Tracks 1, 3, and 5-10
""")


if __name__ == "__main__":
    sys.exit(main())

