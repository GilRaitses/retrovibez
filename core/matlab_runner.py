"""
MATLAB Runner - Executes MATLAB headless for Mason analysis.
"""

import subprocess
import sys
import json
from pathlib import Path


def run_matlab_analysis(input_path: Path, tracks: list, output_dir: Path) -> bool:
    """
    Run MATLAB headless to compute reversal detection.
    
    Args:
        input_path: Path to experiment .mat file or eset directory
        tracks: List of track numbers to process (None = all)
        output_dir: Directory to save results
    
    Returns:
        True if successful, False otherwise
    """
    input_path = Path(input_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find the MATLAB script
    pipeline_root = Path(__file__).parent.parent
    matlab_script = pipeline_root / 'matlab' / 'mason_analysis.m'
    
    if not matlab_script.exists():
        print(f"ERROR: MATLAB script not found: {matlab_script}")
        return False
    
    # Build track string for MATLAB
    if tracks:
        track_str = ','.join(str(t) for t in tracks)
    else:
        track_str = 'all'
    
    # Determine experiment path
    if input_path.is_file():
        expt_path = str(input_path)
    else:
        # It's an eset directory - find the .mat file
        matfiles = input_path / 'matfiles'
        if matfiles.exists():
            mat_files = list(matfiles.glob('*.mat'))
            # Filter out track files
            mat_files = [f for f in mat_files if not f.name.startswith('track')]
            if mat_files:
                expt_path = str(mat_files[0])
            else:
                print(f"ERROR: No experiment .mat file found in {matfiles}")
                return False
        else:
            print(f"ERROR: No matfiles directory found in {input_path}")
            return False
    
    # Build MATLAB command
    matlab_cmd = f"mason_analysis('{expt_path}', '{track_str}', '{str(output_dir)}')"
    
    # Add script directory to MATLAB path
    matlab_full_cmd = f"addpath('{pipeline_root / 'matlab'}'); {matlab_cmd}; exit;"
    
    print(f"Running MATLAB analysis...")
    print(f"  Experiment: {expt_path}")
    print(f"  Tracks: {track_str}")
    print(f"  Output: {output_dir}")
    print()
    
    try:
        # Run MATLAB headless
        result = subprocess.run(
            ['matlab', '-batch', matlab_full_cmd],
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )
        
        if result.returncode != 0:
            print("MATLAB Error Output:")
            print(result.stderr)
            print(result.stdout)
            return False
        
        # Print MATLAB output
        if result.stdout:
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        # Check for success indicator
        summary_file = output_dir / 'analysis_summary.json'
        if summary_file.exists():
            with open(summary_file) as f:
                summary = json.load(f)
            print()
            print(f"Analysis complete:")
            print(f"  Total tracks: {summary.get('total_tracks', 0)}")
            print(f"  Tracks with reversals: {summary.get('tracks_with_reversals', 0)}")
            print(f"  Total reversals: {summary.get('total_reversals', 0)}")
            return True
        else:
            print("WARNING: analysis_summary.json not created. Check MATLAB output.")
            # Still return True if output directory has content
            return any(output_dir.iterdir())
        
    except subprocess.TimeoutExpired:
        print("ERROR: MATLAB analysis timed out (>1 hour)")
        return False
    except FileNotFoundError:
        print("ERROR: MATLAB not found. Make sure MATLAB is installed and in PATH.")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

