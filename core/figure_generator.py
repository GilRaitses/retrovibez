"""
Figure Generator - Creates all visualization plots from analysis results.
Adapted from scripts/2025-12-09/generate_figures_parallel.py
"""

import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import h5py
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed


def load_track_data(track_dir):
    """Load track data from .h5 file"""
    track_dir = Path(track_dir)
    h5_file = track_dir / 'track_data.h5'
    
    if not h5_file.exists():
        raise FileNotFoundError(f"No track_data.h5 found in {track_dir}")
    
    with h5py.File(str(h5_file), 'r') as f:
        data = {
            'track_num': int(np.asarray(f['track_num']).flat[0]),
            'SpeedRunVel': f['SpeedRunVel'][:].ravel(),
            'times': f['times'][:].ravel(),
            'xpos': f['xpos'][:].ravel(),
            'ypos': f['ypos'][:].ravel(),
            'eti': f['eti'][:].ravel(),
        }
        
        data['eset_name'] = f.attrs.get('eset_name', 'unknown')
        if isinstance(data['eset_name'], bytes):
            data['eset_name'] = data['eset_name'].decode('utf-8')
        
        data['lengthPerPixel'] = f.attrs.get('lengthPerPixel', 0.01)
        
        reversals = []
        if 'reversals' in f:
            rev_group = f['reversals']
            for key in sorted(rev_group.keys(), key=lambda x: int(x.replace('reversal_', ''))):
                rev_data = rev_group[key]
                rev_dict = {}
                for field in rev_data.attrs:
                    val = rev_data.attrs[field]
                    rev_dict[field] = float(np.asarray(val).flat[0]) if hasattr(val, '__iter__') else float(val)
                reversals.append(rev_dict)
        
        data['reversals'] = reversals
        
    return data


def create_speed_colormap():
    """Create black-to-white heat colormap for speed visualization"""
    colors = [
        (0.0, 0.0, 0.0), (0.3, 0.0, 0.0), (1.0, 0.0, 0.0),
        (1.0, 0.5, 0.0), (1.0, 1.0, 0.0), (1.0, 1.0, 1.0),
    ]
    return LinearSegmentedColormap.from_list('speed_heatmap', colors, N=256)


def format_time_mmss(seconds):
    """Format seconds as MM:SS"""
    return f"{int(seconds // 60):02d}:{int(seconds % 60):02d}"


def plot_dot_product(track_data, output_path):
    """Generate dot product time series plot with reversal table"""
    times = track_data['times']
    SpeedRunVel = track_data['SpeedRunVel']
    reversals = track_data['reversals']
    track_num = track_data['track_num']
    
    # Build reversal table data
    reversal_table_data = []
    for rev in reversals:
        start_idx = int(rev.get('start_idx', 0))
        end_idx = int(rev.get('end_idx', len(times)))
        if 0 <= start_idx < len(times) and 0 <= end_idx <= len(times):
            rev_times = times[start_idx:end_idx]
            if len(rev_times) > 0:
                duration = float(rev_times[-1] - rev_times[0])
                if duration >= 3.0:
                    reversal_table_data.append({
                        'start': rev_times[0], 'end': rev_times[-1],
                        'duration': duration, 'start_idx': start_idx, 'end_idx': end_idx
                    })
    
    if reversal_table_data:
        fig = plt.figure(figsize=(10, 8), facecolor='white')
        gs = fig.add_gridspec(2, 1, height_ratios=[3, 1], hspace=0.3)
        ax = fig.add_subplot(gs[0])
    else:
        fig = plt.figure(figsize=(10, 6), facecolor='white')
        ax = fig.add_subplot(111)
    
    ax.set_facecolor('white')
    ax.plot(times, SpeedRunVel, 'b-', linewidth=1.5, label='SpeedRun')
    ax.axhline(y=0, color='k', linestyle='--', linewidth=1, label='Zero line')
    
    # Highlight reversals
    for rev_idx, rev_data in enumerate(reversal_table_data):
        rev_times = times[rev_data['start_idx']:rev_data['end_idx']]
        rev_speed = SpeedRunVel[rev_data['start_idx']:rev_data['end_idx']]
        min_len = min(len(rev_times), len(rev_speed))
        if min_len > 0:
            ax.plot(rev_times[:min_len], rev_speed[:min_len], 'r-', linewidth=1.2,
                   label='Reversals (>3s)' if rev_idx == 0 else '')
    
    ax.set_xlabel('Time (seconds)', fontsize=12)
    ax.set_ylabel('SpeedRun (dot product x speed)', fontsize=12)
    title = f'Track {track_num} - Dot Product Over Time'
    if not reversal_table_data:
        title += ' (no reversals >3s)'
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)
    
    # Add reversal table
    if reversal_table_data:
        table_ax = fig.add_subplot(gs[1])
        table_ax.axis('off')
        table_rows = [[f"R{i+1}", format_time_mmss(r['start']), format_time_mmss(r['end']), format_time_mmss(r['duration'])]
                      for i, r in enumerate(reversal_table_data)]
        table = table_ax.table(cellText=table_rows, colLabels=['#', 'Start', 'End', 'Duration'],
                              cellLoc='center', loc='center', bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        for i in range(4):
            table[(0, i)].set_facecolor('#E0E0E0')
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def plot_trajectory(track_data, output_path):
    """Generate trajectory plot with speed coloring"""
    fig = plt.figure(figsize=(9, 9), facecolor=[0.2, 0.2, 0.2])
    ax = fig.add_subplot(111, facecolor=[0.2, 0.2, 0.2])
    
    xpos, ypos, eti = track_data['xpos'], track_data['ypos'], track_data['eti']
    reversals = track_data['reversals']
    
    # Compute speeds
    speeds = []
    for i in range(len(xpos) - 1):
        dx, dy = xpos[i+1] - xpos[i], ypos[i+1] - ypos[i]
        dt = eti[i+1] - eti[i] if i+1 < len(eti) else 1
        speeds.append(np.sqrt(dx**2 + dy**2) / dt * 10 if dt > 0 else 0)
    
    speeds = np.array(speeds)
    speed_min = speeds[speeds > 0].min() if np.any(speeds > 0) else 0
    speed_max = speeds.max() if len(speeds) > 0 else 1
    
    speed_cmap = create_speed_colormap()
    uv_color = np.array([0.5, 0, 1])  # Purple for reversals
    
    # Plot trajectory segments
    for i in range(len(xpos) - 1):
        if i < len(speeds) and speeds[i] > 0:
            speed_norm = (speeds[i] - speed_min) / (speed_max - speed_min + 1e-10)
            line_color = speed_cmap(speed_norm)
            # Check if in reversal
            for rev in reversals:
                if int(rev.get('start_idx', 0)) <= i < int(rev.get('end_idx', len(xpos))):
                    line_color = uv_color
                    break
            ax.plot([xpos[i], xpos[i+1]], [ypos[i], ypos[i+1]], color=line_color, linewidth=2)
    
    ax.set_xlabel('X (cm)', fontsize=12, color='white')
    ax.set_ylabel('Y (cm)', fontsize=12, color='white')
    ax.set_title(f'Track {track_data["track_num"]} - Trajectory', fontsize=14, fontweight='bold', color='white')
    ax.tick_params(colors='white')
    for spine in ax.spines.values():
        spine.set_color('white')
    ax.grid(True, alpha=0.3, color=[0.5, 0.5, 0.5])
    ax.set_aspect('equal')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor=[0.2, 0.2, 0.2])
    plt.close()


def plot_reversal_closeup(track_data, reversal_idx, output_path):
    """Generate close-up dot product for a specific reversal"""
    times, SpeedRunVel = track_data['times'], track_data['SpeedRunVel']
    reversals = track_data['reversals']
    
    if len(reversals) <= reversal_idx:
        return
    
    rev = reversals[reversal_idx]
    start_idx, end_idx = int(rev.get('start_idx', 0)), int(rev.get('end_idx', len(times)))
    
    fig, ax = plt.subplots(figsize=(8, 5), facecolor='white')
    padding = int(0.1 * (end_idx - start_idx))
    view_start, view_end = max(0, start_idx - padding), min(len(times), end_idx + padding)
    
    ax.plot(times[view_start:view_end], SpeedRunVel[view_start:view_end], 'b-', linewidth=2)
    ax.axhline(y=0, color='k', linestyle='--', linewidth=1)
    ax.fill_between(times[start_idx:end_idx], SpeedRunVel[start_idx:end_idx], 0, color='r', alpha=0.5)
    
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('SpeedRun')
    ax.set_title(f'Track {track_data["track_num"]} - Reversal {reversal_idx + 1}', fontweight='bold')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
    plt.close()


def process_single_track(args):
    """Process a single track - called by parallel executor"""
    track_num, results_dir, figures_dir = args
    track_dir = Path(results_dir) / f'track{track_num}'
    
    if not track_dir.exists():
        return {'track_num': track_num, 'status': 'not_found', 'reversals': 0}
    
    try:
        data = load_track_data(track_dir)
        track_fig_dir = Path(figures_dir) / f'track{track_num}'
        track_fig_dir.mkdir(exist_ok=True)
        
        # Generate main figures
        plot_dot_product(data, track_fig_dir / 'dot_product.png')
        plot_trajectory(data, track_fig_dir / 'trajectory.png')
        
        # Generate reversal-specific figures
        for r_idx in range(len(data['reversals'])):
            plot_reversal_closeup(data, r_idx, track_fig_dir / f'reversal{r_idx+1}_dot_product.png')
        
        return {
            'track_num': track_num,
            'status': 'success',
            'reversals': len(data['reversals'])
        }
    except Exception as e:
        return {'track_num': track_num, 'status': 'error', 'error': str(e), 'reversals': 0}


def generate_all_figures(results_dir: Path, figures_dir: Path, tracks: list = None):
    """
    Generate all figures for processed tracks.
    
    Args:
        results_dir: Directory containing track results (track_data.h5 files)
        figures_dir: Directory to save generated figures
        tracks: List of track numbers to process (None = auto-detect)
    """
    results_dir = Path(results_dir)
    figures_dir = Path(figures_dir)
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Auto-detect tracks if not specified
    if tracks is None:
        track_dirs = sorted([
            int(d.name.replace('track', ''))
            for d in results_dir.iterdir()
            if d.is_dir() and d.name.startswith('track')
        ])
        tracks = track_dirs
    
    if not tracks:
        print("No tracks to process.")
        return
    
    print(f"Generating figures for {len(tracks)} tracks...")
    
    # Prepare args for parallel processing
    args_list = [(t, results_dir, figures_dir) for t in tracks]
    
    results = []
    max_workers = min(4, len(tracks))
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_single_track, args): args[0] for args in args_list}
        for future in as_completed(futures):
            track_num = futures[future]
            try:
                result = future.result()
                results.append(result)
                status = result['status']
                revs = result['reversals']
                print(f"  Track {track_num}: {status} ({revs} reversals)")
            except Exception as e:
                print(f"  Track {track_num}: exception - {e}")
                results.append({'track_num': track_num, 'status': 'exception', 'reversals': 0})
    
    # Summary
    success = sum(1 for r in results if r['status'] == 'success')
    total_revs = sum(r['reversals'] for r in results)
    print(f"\nFigure generation complete: {success}/{len(tracks)} tracks, {total_revs} total reversals")
    
    # Save summary
    with open(figures_dir / 'summary.json', 'w') as f:
        json.dump({'tracks': results, 'total_reversals': total_revs}, f, indent=2)

