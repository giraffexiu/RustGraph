#!/usr/bin/env python3
"""
Build script for rust-analyzer binary during pip install
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def check_rust_installed():
    """Check if Rust and Cargo are installed"""
    try:
        result = subprocess.run(['cargo', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"Found Cargo: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_rust():
    """Install Rust using rustup"""
    print("Rust not found. Attempting to install Rust...")
    
    # First, try to add cargo to PATH if it exists but wasn't found
    cargo_bin = Path.home() / '.cargo' / 'bin'
    if cargo_bin.exists():
        print(f"Found cargo directory at {cargo_bin}, adding to PATH...")
        os.environ['PATH'] = f"{cargo_bin}:{os.environ.get('PATH', '')}"
        if check_rust_installed():
            return True
    
    try:
        # Download and run rustup installer
        if platform.system() == "Windows":
            print("Windows detected. Please install Rust manually:")
            print("1. Visit: https://rustup.rs/")
            print("2. Download and run rustup-init.exe")
            print("3. Restart your terminal and try again")
            return False
        else:
            # For Unix-like systems
            print("Downloading rustup installer...")
            subprocess.run([
                'curl', '--proto', '=https', '--tlsv1.2', '-sSf', 
                'https://sh.rustup.rs', '-o', '/tmp/rustup.sh'
            ], check=True)
            
            print("Installing Rust...")
            subprocess.run(['sh', '/tmp/rustup.sh', '-y'], check=True)
            
            # Add cargo to PATH for this session
            cargo_bin = Path.home() / '.cargo' / 'bin'
            if cargo_bin.exists():
                os.environ['PATH'] = f"{cargo_bin}:{os.environ.get('PATH', '')}"
            
            # Clean up installer
            try:
                os.remove('/tmp/rustup.sh')
            except:
                pass
            
            return check_rust_installed()
    except subprocess.CalledProcessError as e:
        print(f"Failed to install Rust: {e}")
        print("Please install Rust manually:")
        print("  Visit: https://rustup.rs/")
        print("  Or run: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
        return False


def build_rust_analyzer():
    """Build the custom rust-analyzer binary"""
    print("Building custom rust-analyzer...")
    
    # Get the project root directory
    project_root = Path(__file__).parent
    
    try:
        # Build in release mode
        result = subprocess.run([
            'cargo', 'build', '--release', '--bin', 'rust-analyzer'
        ], cwd=project_root, capture_output=True, text=True, check=True)
        
        print("rust-analyzer built successfully!")
        
        # Check if binary exists
        binary_path = project_root / 'target' / 'release' / 'rust-analyzer'
        if platform.system() == "Windows":
            binary_path = binary_path.with_suffix('.exe')
            
        if binary_path.exists():
            print(f"Binary created at: {binary_path}")
            return binary_path
        else:
            print("Binary not found after build")
            return None
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to build rust-analyzer: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return None


def copy_binary_to_package():
    """Copy the built binary to the package directory"""
    project_root = Path(__file__).parent
    binary_path = project_root / 'target' / 'release' / 'rust-analyzer'
    
    if platform.system() == "Windows":
        binary_path = binary_path.with_suffix('.exe')
    
    if not binary_path.exists():
        print(f"Binary not found at {binary_path}")
        return False
    
    # Create bin directory in package
    package_bin_dir = project_root / 'solana_fcg_tool' / 'bin'
    package_bin_dir.mkdir(exist_ok=True)
    
    # Copy binary
    import shutil
    target_binary = package_bin_dir / binary_path.name
    shutil.copy2(binary_path, target_binary)
    
    # Make executable on Unix-like systems
    if platform.system() != "Windows":
        os.chmod(target_binary, 0o755)
    
    print(f"Binary copied to: {target_binary}")
    return True


def main():
    """Main build function"""
    print("=" * 50)
    print("Building Solana FCG Tool with custom rust-analyzer")
    print("=" * 50)
    
    # Check if Rust is installed
    if not check_rust_installed():
        print("Rust/Cargo not found. Attempting to install...")
        if not install_rust():
            print("ERROR: Could not install Rust. Please install manually:")
            print("  Visit: https://rustup.rs/")
            print("  Or run: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh")
            sys.exit(1)
    
    # Build rust-analyzer
    binary_path = build_rust_analyzer()
    if not binary_path:
        print("ERROR: Failed to build rust-analyzer")
        sys.exit(1)
    
    # Copy binary to package
    if not copy_binary_to_package():
        print("ERROR: Failed to copy binary to package")
        sys.exit(1)
    
    print("=" * 50)
    print("Build completed successfully!")
    print("=" * 50)


if __name__ == '__main__':
    main()