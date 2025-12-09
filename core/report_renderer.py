"""
Report Renderer - Renders QMD files to PDF and HTML using Quarto.
"""

import subprocess
from pathlib import Path


def render_report(qmd_path: Path) -> bool:
    """
    Render a QMD file to PDF and HTML using Quarto.
    
    Args:
        qmd_path: Path to the QMD file
    
    Returns:
        True if successful, False otherwise
    """
    qmd_path = Path(qmd_path)
    
    if not qmd_path.exists():
        print(f"ERROR: QMD file not found: {qmd_path}")
        return False
    
    print(f"Rendering report: {qmd_path.name}")
    
    try:
        # Render to both PDF and HTML
        result = subprocess.run(
            ['quarto', 'render', str(qmd_path), '--to', 'pdf,html'],
            capture_output=True,
            text=True,
            cwd=qmd_path.parent,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            print("Quarto Error:")
            print(result.stderr)
            
            # Try rendering formats separately
            print("\nTrying PDF only...")
            pdf_result = subprocess.run(
                ['quarto', 'render', str(qmd_path), '--to', 'pdf'],
                capture_output=True,
                text=True,
                cwd=qmd_path.parent,
                timeout=300
            )
            
            print("Trying HTML only...")
            html_result = subprocess.run(
                ['quarto', 'render', str(qmd_path), '--to', 'html'],
                capture_output=True,
                text=True,
                cwd=qmd_path.parent,
                timeout=300
            )
            
            if pdf_result.returncode != 0 and html_result.returncode != 0:
                return False
        
        # Check output files
        pdf_path = qmd_path.with_suffix('.pdf')
        html_path = qmd_path.with_suffix('.html')
        
        if pdf_path.exists():
            print(f"  PDF: {pdf_path.name}")
        else:
            print("  PDF: not generated")
        
        if html_path.exists():
            print(f"  HTML: {html_path.name}")
        else:
            print("  HTML: not generated")
        
        return pdf_path.exists() or html_path.exists()
        
    except subprocess.TimeoutExpired:
        print("ERROR: Quarto rendering timed out (>5 minutes)")
        return False
    except FileNotFoundError:
        print("ERROR: Quarto not found. Make sure Quarto is installed and in PATH.")
        print("  Install from: https://quarto.org/docs/get-started/")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False

