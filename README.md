# RetroVibez 🔄

**Larval Reversal Detection Pipeline** | v1.0.0

Automated end-to-end pipeline for detecting and analyzing reverse crawling behavior in *Drosophila* larvae. Computes heading-velocity dot products, identifies reversal events, generates trajectory visualizations, and renders PDF/HTML reports.

**Author:** Gil Raitses  
**Lab:** Bhattacharya Lab (Mirna Lab), BioInspired Institute, Syracuse University  
**Date:** December 9, 2025  
**License:** MIT (see [LICENSE](LICENSE))

---

## Quick Start

### Windows
```cmd
retrovibez.bat install   # First time: install dependencies
retrovibez.bat           # Run analysis
```

### macOS
```bash
chmod +x retrovibez.command retrovibez.sh
./retrovibez.sh install  # First time: install dependencies
./retrovibez.sh          # Run analysis
# Or double-click retrovibez.command in Finder
```

### Linux
```bash
chmod +x retrovibez.sh
./retrovibez.sh install  # First time: install dependencies
./retrovibez.sh          # Run analysis
```

---

## Features

- **Cross-platform** - Windows, macOS, Linux
- **Interactive CLI** - Drag-and-drop or type paths
- **Flexible track selection** - `all`, `1,2,5`, `1-10`, or `1,3,5-10,15`
- **Auto-detection** - Handles experiments, esets, or collections
- **Dual track formats** - Separate track files OR embedded in MAT
- **Parallel processing** - Figure generation on multiple cores
- **Automatic reports** - QMD to PDF/HTML with embedded figures

## How It Works

The pipeline detects **reverse crawling** by computing the dot product between:
- **Heading vector**: Direction the larva's head is pointing (head → midpoint)
- **Velocity vector**: Direction of movement

When `SpeedRunVel < 0` for ≥3 seconds, a reversal event is recorded.

## Requirements

| Component | Version | Check |
|-----------|---------|-------|
| Python | >= 3.8 | `python --version` |
| MATLAB | Any recent | `matlab -batch "disp('ok')"` |
| Quarto | >= 1.3 | `quarto --version` |
| numpy | >= 1.20 | `pip show numpy` |
| matplotlib | >= 3.5 | `pip show matplotlib` |
| h5py | >= 3.0 | `pip show h5py` |

## Installation

### Windows (Non-Interactive)
```powershell
pip install -r requirements.txt
winget install Posit.Quarto --accept-source-agreements --accept-package-agreements
```

### macOS
```bash
pip3 install -r requirements.txt
brew install quarto
```

### Linux (Debian/Ubuntu)
```bash
pip3 install -r requirements.txt
# Download Quarto .deb from https://quarto.org/docs/download/
sudo dpkg -i quarto-*.deb
```

### Verify Installation
```bash
# Windows
retrovibez.bat check

# macOS/Linux
./retrovibez.sh check
```

## Usage

1. **Launch** - Double-click `retrovibez.bat` (Win) or `retrovibez.command` (Mac)
2. **Path** - Drag a folder into the terminal or type a path
3. **Tracks** - Select: `all`, `1,2,5`, `1-10`, or `1,3,5-10,15`
4. **Output** - Choose output directory (or accept default)
5. **Run** - Pipeline executes automatically

### Track Selection Syntax

| Input | Meaning |
|-------|---------|
| `all` | All tracks in experiment |
| `1,2,5` | Tracks 1, 2, and 5 |
| `1-10` | Tracks 1 through 10 |
| `1,3,5-10,15` | Tracks 1, 3, 5-10, and 15 |

## Supported Data Formats

RetroVibez handles two common MAGAT data layouts:

1. **Separate track files** (default MAGAT):
   ```
   matfiles/
   ├── experiment.mat
   └── GMR61@GMR61_202510291652 - tracks/
       ├── track1.mat
       ├── track2.mat
       └── ...
   ```

2. **Embedded tracks** (tracks saved back to experiment):
   ```
   matfiles/
   └── experiment.mat  # Contains eset.expt.track array
   ```

The pipeline auto-detects which format is used.

## Pipeline Stages

```
1. MATLAB Analysis (headless)
   └── Computes SpeedRunVel, detects reversals (≥3s)
   └── Outputs: results/trackN/track_data.h5

2. Figure Generation (parallel Python)
   └── Trajectory plots (speed-colored, reversals in purple)
   └── Dot product time series
   └── Reversal close-ups
   └── Outputs: figures/trackN/*.png

3. QMD Report Generation
   └── Auto-builds Quarto document from data
   └── Embeds all figures

4. Rendering (Quarto)
   └── PDF and HTML output
```

## Output Structure

```
output_dir/
├── results/
│   ├── analysis_summary.json
│   └── trackN/
│       └── track_data.h5
├── figures/
│   ├── summary.json
│   └── trackN/
│       ├── dot_product.png
│       ├── trajectory.png
│       └── reversalN_dot_product.png
├── retrovibez_report.qmd
├── retrovibez_report.pdf
└── retrovibez_report.html
```

## Attribution

This pipeline implements the reverse crawling detection methods described in:

> Klein M, Afonso B, Vonner AJ, Hernandez-Nunez L, Berck M, Taber CJ, Cardona A, Zlatic M, Samuel ADT. (2015). Sensory determinants of behavioral dynamics in *Drosophila* thermotaxis. *PNAS*, 112(2), E220-E229. https://doi.org/10.1073/pnas.1416212112

Raw behavioral data: [Harvard Dataverse](https://doi.org/10.7910/DVN/9JWPN2)

**See [CITATION.md](CITATION.md) for full citation details and BibTeX.**

## License

MIT License - See [LICENSE](LICENSE)

When publishing figures generated with this tool, please cite both RetroVibez and Klein et al. (2015).

## Troubleshooting

### MATLAB not found
Add MATLAB to PATH:
```bash
# Windows PowerShell
$env:PATH += ";C:\Program Files\MATLAB\R2024a\bin"

# macOS/Linux
export PATH="/Applications/MATLAB_R2024a.app/bin:$PATH"
```

### Quarto rendering fails
Install TinyTeX for PDF support:
```bash
quarto install tinytex
```

### Python packages missing
```bash
pip install numpy matplotlib h5py
```

## Files

| File | Description |
|------|-------------|
| `retrovibez.bat` | Windows launcher |
| `retrovibez.sh` | Linux launcher |
| `retrovibez.command` | macOS launcher (double-click) |
| `retrovibez_cli.py` | Main CLI entry point |
| `requirements.txt` | Python dependencies |
| `VERSION` | Current version (1.0.0) |
| `core/systemfairy.py` | Environment checker |
| `core/matlab_runner.py` | MATLAB headless executor |
| `core/figure_generator.py` | Parallel figure generation |
| `core/qmd_generator.py` | Report builder |
| `core/report_renderer.py` | Quarto renderer |
| `matlab/mason_analysis.m` | MATLAB analysis script |
