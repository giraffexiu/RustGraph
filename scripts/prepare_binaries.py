#!/usr/bin/env python3
"""
Prepare binary directory structure for multi-platform builds
"""

import os
import shutil
import platform
from pathlib import Path


def get_platform_binary_name():
    """Get the appropriate binary name for the current platform"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "linux":
        if machine in ["x86_64", "amd64"]:
            return "rust-analyzer-linux-x86_64"
    elif system == "darwin":  # macOS
        if machine in ["x86_64", "amd64"]:
            return "rust-analyzer-macos-x86_64"
        elif machine in ["arm64", "aarch64"]:
            return "rust-analyzer-macos-aarch64"
    elif system == "windows":
        if machine in ["x86_64", "amd64"]:
            return "rust-analyzer-windows-x86_64.exe"
    
    # Fallback to generic name
    return "rust-analyzer"


def main():
    print("Preparing binary directory structure...")
    
    bin_dir = Path("solana_fcg_tool/bin")
    
    # Check if generic binary exists
    generic_binary = "rust-analyzer"
    if platform.system() == "Windows":
        generic_binary = "rust-analyzer.exe"
    
    generic_path = bin_dir / generic_binary
    
    if not generic_path.exists():
        print(f"Error: Generic binary {generic_path} not found!")
        return 1
    
    # Get platform-specific name
    platform_binary = get_platform_binary_name()
    platform_path = bin_dir / platform_binary
    
    print(f"Current platform: {platform.system()} {platform.machine()}")
    print(f"Generic binary: {generic_path}")
    print(f"Platform binary: {platform_path}")
    
    # Copy generic binary to platform-specific name
    if not platform_path.exists():
        print(f"Copying {generic_path} to {platform_path}")
        shutil.copy2(generic_path, platform_path)
        
        # Make sure it's executable (Unix only)
        if platform.system() != "Windows":
            os.chmod(platform_path, 0o755)
        
        print("✓ Platform-specific binary created")
    else:
        print("✓ Platform-specific binary already exists")
    
    # List all binaries
    print("\nBinaries in bin directory:")
    for file in sorted(bin_dir.iterdir()):
        if file.is_file():
            size = file.stat().st_size
            print(f"  - {file.name} ({size:,} bytes)")
    
    print("\n✓ Binary directory prepared successfully!")
    return 0


if __name__ == "__main__":
    exit(main())