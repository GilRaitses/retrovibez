"""
QMD Generator - Programmatically builds Quarto Markdown reports from analysis results.
"""

import json
from pathlib import Path
from datetime import datetime


def generate_qmd_report(results_dir: Path, figures_dir: Path, output_dir: Path) -> Path:
    """
    Generate a QMD report by reading analysis results and embedding figures.
    
    Args:
        results_dir: Directory containing analysis_summary.json and track results
        figures_dir: Directory containing generated figures
        output_dir: Directory to write the QMD file
    
    Returns:
        Path to the generated QMD file
    """
    results_dir = Path(results_dir)
    figures_dir = Path(figures_dir)
    output_dir = Path(output_dir)
    
    # Load analysis summary
    summary_file = results_dir / 'analysis_summary.json'
    if summary_file.exists():
        with open(summary_file) as f:
            summary = json.load(f)
    else:
        summary = {'experiment': 'Unknown', 'total_tracks': 0}
    
    # Load figure summary
    fig_summary_file = figures_dir / 'summary.json'
    if fig_summary_file.exists():
        with open(fig_summary_file) as f:
            fig_summary = json.load(f)
    else:
        fig_summary = {'tracks': []}
    
    # Get experiment info
    experiment_name = summary.get('experiment', 'Unknown')
    timestamp = summary.get('timestamp', datetime.now().strftime("%Y%m%d%H%M%S"))
    
    # Find all track directories with figures
    track_dirs = sorted([
        d for d in figures_dir.iterdir()
        if d.is_dir() and d.name.startswith('track')
    ], key=lambda x: int(x.name.replace('track', '')))
    
    # Build QMD content
    qmd_lines = []
    
    # YAML header with Tokyo Night theme
    qmd_lines.append('---')
    qmd_lines.append(f'title: "RetroVibez Analysis: {experiment_name}"')
    qmd_lines.append(f'subtitle: "Timestamp: {timestamp}"')
    qmd_lines.append(f'date: "{datetime.now().strftime("%Y-%m-%d")}"')
    qmd_lines.append('highlight-style: templates/tokyo-night.theme')
    qmd_lines.append('format:')
    qmd_lines.append('  pdf:')
    qmd_lines.append('    toc: true')
    qmd_lines.append('    toc-depth: 2')
    qmd_lines.append('    geometry:')
    qmd_lines.append('      - margin=1in')
    qmd_lines.append('    code-block-bg: "#1a1b26"')
    qmd_lines.append('    code-block-border-left: "#7aa2f7"')
    qmd_lines.append('  html:')
    qmd_lines.append('    toc: true')
    qmd_lines.append('    toc-depth: 2')
    qmd_lines.append('    embed-resources: true')
    qmd_lines.append('    theme:')
    qmd_lines.append('      dark: darkly')
    qmd_lines.append('    code-block-bg: "#1a1b26"')
    qmd_lines.append('    code-block-border-left: "#7aa2f7"')
    qmd_lines.append('---')
    qmd_lines.append('')
    
    # Summary section
    qmd_lines.append('# Summary')
    qmd_lines.append('')
    qmd_lines.append(f"**Experiment:** {experiment_name}")
    qmd_lines.append('')
    qmd_lines.append(f"**Timestamp:** {timestamp}")
    qmd_lines.append('')
    qmd_lines.append(f"**Total Tracks Analyzed:** {summary.get('total_tracks', len(track_dirs))}")
    qmd_lines.append('')
    qmd_lines.append(f"**Tracks with Reversals:** {summary.get('tracks_with_reversals', 'N/A')}")
    qmd_lines.append('')
    qmd_lines.append(f"**Total Reversals Detected:** {summary.get('total_reversals', 'N/A')}")
    qmd_lines.append('')
    
    if summary.get('avg_reversal_duration'):
        qmd_lines.append(f"**Average Reversal Duration:** {summary.get('avg_reversal_duration'):.2f} s")
        qmd_lines.append('')
        qmd_lines.append(f"**Min/Max Duration:** {summary.get('min_reversal_duration'):.2f} s / {summary.get('max_reversal_duration'):.2f} s")
        qmd_lines.append('')
    
    qmd_lines.append('---')
    qmd_lines.append('')
    
    # Track sections
    qmd_lines.append('# Individual Track Analysis')
    qmd_lines.append('')
    
    for track_dir in track_dirs:
        track_num = int(track_dir.name.replace('track', ''))
        
        qmd_lines.append(f'## Track {track_num}')
        qmd_lines.append('')
        
        # Find track info from fig_summary
        track_info = next(
            (t for t in fig_summary.get('tracks', []) if t.get('track_num') == track_num),
            {'reversals': 0}
        )
        num_reversals = track_info.get('reversals', 0)
        
        qmd_lines.append(f"**Reversals detected:** {num_reversals}")
        qmd_lines.append('')
        
        # Dot product figure (relative path from output_dir to figures_dir)
        rel_figures = figures_dir.relative_to(output_dir) if figures_dir.is_relative_to(output_dir) else figures_dir
        
        dot_product_path = track_dir / 'dot_product.png'
        if dot_product_path.exists():
            rel_path = f"{rel_figures.name}/{track_dir.name}/dot_product.png"
            qmd_lines.append(f'### Dot Product Over Time')
            qmd_lines.append('')
            qmd_lines.append(f'![Track {track_num} - Dot Product]({rel_path}){{width=100%}}')
            qmd_lines.append('')
        
        # Trajectory figure
        trajectory_path = track_dir / 'trajectory.png'
        if trajectory_path.exists():
            rel_path = f"{rel_figures.name}/{track_dir.name}/trajectory.png"
            qmd_lines.append(f'### Trajectory')
            qmd_lines.append('')
            qmd_lines.append(f'![Track {track_num} - Trajectory]({rel_path}){{width=80%}}')
            qmd_lines.append('')
        
        # Reversal-specific figures
        if num_reversals > 0:
            qmd_lines.append(f'### Reversal Details')
            qmd_lines.append('')
            
            for r_idx in range(1, num_reversals + 1):
                rev_dot_path = track_dir / f'reversal{r_idx}_dot_product.png'
                if rev_dot_path.exists():
                    rel_path = f"{rel_figures.name}/{track_dir.name}/reversal{r_idx}_dot_product.png"
                    qmd_lines.append(f'#### Reversal {r_idx}')
                    qmd_lines.append('')
                    qmd_lines.append(f'![Reversal {r_idx} Close-up]({rel_path}){{width=90%}}')
                    qmd_lines.append('')
        
        qmd_lines.append('---')
        qmd_lines.append('')
        qmd_lines.append('\\newpage')
        qmd_lines.append('')
    
    # Write QMD file
    qmd_content = '\n'.join(qmd_lines)
    qmd_path = output_dir / 'mason_analysis_report.qmd'
    
    with open(qmd_path, 'w', encoding='utf-8') as f:
        f.write(qmd_content)
    
    print(f"Generated QMD report: {qmd_path}")
    print(f"  Tracks documented: {len(track_dirs)}")
    
    return qmd_path

