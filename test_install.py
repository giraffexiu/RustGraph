#!/usr/bin/env python3
"""
Test script to simulate pip install process
"""

import subprocess
import sys
import tempfile
import shutil
from pathlib import Path


def test_source_distribution():
    """Test creating and installing from source distribution"""
    print("=" * 60)
    print("Testing source distribution build and install")
    print("=" * 60)
    
    # Create source distribution
    print("1. Creating source distribution...")
    result = subprocess.run([sys.executable, 'setup.py', 'sdist'], 
                          capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Failed to create sdist: {result.stderr}")
        return False
    
    print("✓ Source distribution created successfully")
    
    # Find the created tarball
    dist_dir = Path('dist')
    tarballs = list(dist_dir.glob('*.tar.gz'))
    if not tarballs:
        print("No tarball found in dist/")
        return False
    
    tarball = tarballs[-1]  # Get the latest one
    print(f"✓ Found tarball: {tarball}")
    
    # Create a temporary virtual environment for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        venv_path = temp_path / 'test_venv'
        
        print("2. Creating test virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', str(venv_path)], check=True)
        
        # Get the python executable in the venv
        if sys.platform == "win32":
            python_exe = venv_path / 'Scripts' / 'python.exe'
            pip_exe = venv_path / 'Scripts' / 'pip.exe'
        else:
            python_exe = venv_path / 'bin' / 'python'
            pip_exe = venv_path / 'bin' / 'pip'
        
        print("3. Installing package in test environment...")
        result = subprocess.run([str(pip_exe), 'install', str(tarball)], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to install package: {result.stderr}")
            print(f"stdout: {result.stdout}")
            return False
        
        print("✓ Package installed successfully")
        
        # Test if the CLI works
        print("4. Testing CLI functionality...")
        result = subprocess.run([str(python_exe), '-c', 
                               'from solana_fcg_tool.cli import main; print("CLI import successful")'],
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to import CLI: {result.stderr}")
            return False
        
        print("✓ CLI import test passed")
        
        # Test if the analyzer works
        print("5. Testing analyzer functionality...")
        result = subprocess.run([str(python_exe), '-c', 
                               'from solana_fcg_tool import SolanaAnalyzer; print("Analyzer import successful")'],
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Failed to import analyzer: {result.stderr}")
            return False
        
        print("✓ Analyzer import test passed")
    
    print("\n" + "=" * 60)
    print("🎉 All tests passed! The package can be safely uploaded to PyPI.")
    print("=" * 60)
    return True


def main():
    """Main test function"""
    if not test_source_distribution():
        print("❌ Tests failed!")
        return 1
    
    print("\nNext steps:")
    print("1. Upload to PyPI: python -m twine upload dist/*")
    print("2. Test install from PyPI: pip install solana-fcg-tool")
    print("3. Run verification: python verify_installation.py")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())