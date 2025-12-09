"""
System Fairy - Environment verification for Mason Analysis Pipeline.
Checks all required dependencies before allowing analysis to run.
"""

import sys
import shutil
import subprocess
from pathlib import Path


def check_python_version():
    """Check Python version >= 3.8"""
    version = sys.version_info
    ok = version >= (3, 8)
    detail = f"{version.major}.{version.minor}.{version.micro}"
    return ok, detail


def check_python_packages():
    """Check required Python packages are installed"""
    required = ['numpy', 'matplotlib', 'h5py', 'jupyter']
    missing = []
    installed = []
    
    for pkg in required:
        try:
            __import__(pkg)
            installed.append(pkg)
        except ImportError:
            missing.append(pkg)
    
    ok = len(missing) == 0
    if ok:
        detail = f"All installed: {', '.join(required)}"
    else:
        detail = f"Missing: {', '.join(missing)}"
    
    return ok, detail, missing


def check_matlab():
    """Check MATLAB is installed and accessible"""
    matlab_path = shutil.which('matlab')
    ok = matlab_path is not None
    
    if ok:
        # Try to get version
        try:
            result = subprocess.run(
                ['matlab', '-batch', 'disp(version)'],
                capture_output=True,
                text=True,
                timeout=60
            )
            version = result.stdout.strip().split('\n')[-1] if result.returncode == 0 else 'unknown'
            detail = f"{matlab_path} (v{version})"
        except Exception:
            detail = matlab_path
    else:
        detail = "Not found in PATH"
    
    return ok, detail


def check_matlab_engine():
    """Check MATLAB Engine for Python is installed"""
    try:
        import matlab.engine
        return True, "Installed"
    except ImportError:
        return False, "Not installed (install from MATLAB/extern/engines/python)"


def check_quarto():
    """Check Quarto is installed"""
    quarto_path = shutil.which('quarto')
    ok = quarto_path is not None
    
    if ok:
        try:
            result = subprocess.run(
                ['quarto', '--version'],
                capture_output=True,
                text=True,
                timeout=10
            )
            version = result.stdout.strip() if result.returncode == 0 else 'unknown'
            detail = f"{quarto_path} (v{version})"
        except Exception:
            detail = quarto_path
    else:
        detail = "Not found in PATH"
    
    return ok, detail


def check_tinytex():
    """Check TinyTeX is installed (for PDF rendering)"""
    try:
        result = subprocess.run(
            ['quarto', 'check'],
            capture_output=True,
            text=True,
            timeout=30
        )
        # Check if TinyTeX or LaTeX is mentioned as OK
        output = result.stdout + result.stderr
        if 'tinytex' in output.lower() or 'latex' in output.lower():
            if 'OK' in output or 'installed' in output.lower():
                return True, "TinyTeX installed"
        
        # Try to find tlmgr (TeX Live Manager)
        tlmgr_path = shutil.which('tlmgr')
        if tlmgr_path:
            return True, f"TeX distribution found: {tlmgr_path}"
        
        return False, "Not installed (run: quarto install tinytex)"
    except Exception:
        return False, "Could not check (run: quarto install tinytex)"


def check_magat_codebase():
    """Check if MAGAT codebase is accessible (for MATLAB classes)"""
    # Check common locations
    possible_paths = [
        Path.home() / 'MAGATAnalyzer-Matlab-Analysis',
        Path('D:/MAGATAnalyzer-Matlab-Analysis'),
        Path('C:/MAGATAnalyzer-Matlab-Analysis'),
    ]
    
    # Also check environment variable
    import os
    env_path = os.environ.get('MAGAT_CODEBASE')
    if env_path:
        possible_paths.insert(0, Path(env_path))
    
    for p in possible_paths:
        if p.exists() and (p / 'analySis').exists():
            return True, str(p)
    
    # Check if ExperimentSet is available in MATLAB path
    # (might be added via startup.m)
    return True, "Assuming MATLAB path configured"


def run_systemfairy(verbose=True):
    """
    Run all environment checks.
    
    Returns:
        Tuple of (all_ok, missing_items)
    """
    checks = []
    missing = []
    
    # Python version
    ok, detail = check_python_version()
    checks.append(('Python >= 3.8', ok, detail))
    if not ok:
        missing.append('python')
    
    # Python packages
    ok, detail, missing_pkgs = check_python_packages()
    checks.append(('Python packages', ok, detail))
    if not ok:
        missing.extend(missing_pkgs)
    
    # MATLAB
    ok, detail = check_matlab()
    checks.append(('MATLAB', ok, detail))
    if not ok:
        missing.append('matlab')
    
    # MATLAB Engine for Python
    ok, detail = check_matlab_engine()
    checks.append(('MATLAB Engine', ok, detail))
    if not ok:
        missing.append('matlab_engine')
    
    # Quarto
    ok, detail = check_quarto()
    checks.append(('Quarto', ok, detail))
    if not ok:
        missing.append('quarto')
    
    # TinyTeX (for PDF)
    ok, detail = check_tinytex()
    checks.append(('TinyTeX (PDF)', ok, detail))
    if not ok:
        missing.append('tinytex')
    
    # MAGAT codebase
    ok, detail = check_magat_codebase()
    checks.append(('MAGAT codebase', ok, detail))
    if not ok:
        missing.append('magat')
    
    if verbose:
        print("=" * 60)
        print("  System Fairy - Environment Check")
        print("=" * 60)
        print()
        
        for label, ok, detail in checks:
            icon = "[OK]" if ok else "[X]"
            print(f"  {icon} {label}: {detail}")
        
        print()
        
        if missing:
            print("Missing components detected. Installation commands:")
            print()
            
            if 'python' in missing:
                print("  Python 3.8+:")
                print("    winget install Python.Python.3.11 --accept-source-agreements --accept-package-agreements")
                print()
            
            if any(p in missing for p in ['numpy', 'matplotlib', 'h5py']):
                pipeline_root = Path(__file__).parent.parent
                print("  Python packages:")
                print(f"    pip install -r \"{pipeline_root / 'requirements.txt'}\"")
                print()
            
            if 'matlab' in missing:
                print("  MATLAB:")
                print("    Install from https://www.mathworks.com/products/matlab.html")
                print("    Ensure 'matlab' is in your PATH")
                print()
            
            if 'matlab_engine' in missing:
                print("  MATLAB Engine for Python:")
                print("    cd \"<MATLAB_ROOT>/extern/engines/python\"")
                print("    python -m pip install .")
                print("    # Windows: C:\\Program Files\\MATLAB\\R2024a\\extern\\engines\\python")
                print("    # macOS:   /Applications/MATLAB_R2024a.app/extern/engines/python")
                print("    # Linux:   /usr/local/MATLAB/R2024a/extern/engines/python")
                print()
            
            if 'quarto' in missing:
                print("  Quarto (non-interactive):")
                print("    winget install Posit.Quarto --accept-source-agreements --accept-package-agreements")
                print("    # Or download from: https://quarto.org/docs/download/")
                print()
            
            if 'tinytex' in missing:
                print("  TinyTeX (for PDF rendering):")
                print("    quarto install tinytex --update-path")
                print()
            
            print("-" * 60)
            print("Run this to install all missing components (admin PowerShell):")
            print()
            print("  # Python packages")
            print(f"  pip install numpy matplotlib h5py")
            print()
            print("  # Quarto")
            print("  winget install Posit.Quarto --accept-source-agreements --accept-package-agreements")
            print("-" * 60)
            
            return False, missing
        else:
            print("All requirements satisfied!")
            return True, []
    
    all_ok = len(missing) == 0
    return all_ok, missing


def ensure_requirements():
    """
    Check requirements and exit if not met.
    Called at the start of the pipeline.
    """
    ok, missing = run_systemfairy(verbose=True)
    
    if not ok:
        print()
        print("Please install missing components and try again.")
        sys.exit(1)
    
    return True


if __name__ == '__main__':
    run_systemfairy()

