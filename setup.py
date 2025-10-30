#!/usr/bin/env python3
"""
Setup script for Solana Analyzer package with multi-platform binary support
"""

import os
import sys
import platform
import shutil
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.install import install
from pathlib import Path

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""


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


class PlatformBinaryHandler:
    """Mixin class to handle platform-specific binary selection"""
    
    def setup_platform_binary(self):
        """Setup the correct binary for the current platform"""
        print(f"Setting up binary for platform: {platform.system()} {platform.machine()}")
        
        package_bin_dir = Path("solana_fcg_tool") / "bin"
        package_bin_dir.mkdir(exist_ok=True)
        
        platform_binary_name = get_platform_binary_name()
        platform_binary_path = package_bin_dir / platform_binary_name
        target_binary_path = package_bin_dir / "rust-analyzer"
        
        # If we're in CI/CD environment, the binaries should already be placed
        if platform_binary_path.exists():
            print(f"Found platform-specific binary: {platform_binary_path}")
            
            # Copy platform-specific binary to generic name
            if target_binary_path.exists():
                target_binary_path.unlink()
            
            shutil.copy2(platform_binary_path, target_binary_path)
            
            # Make executable on Unix systems
            if platform.system() != "Windows":
                os.chmod(target_binary_path, 0o755)
            
            print(f"Binary setup complete: {target_binary_path}")
            return True
        
        # If platform-specific binary doesn't exist, try to build locally
        elif not target_binary_path.exists():
            print("Platform-specific binary not found, attempting local build...")
            return self.build_rust_analyzer()
        
        return True
    
    def build_rust_analyzer(self):
        """Build the rust-analyzer binary locally"""
        print("Building custom rust-analyzer binary...")
        
        try:
            from build_rust import main as build_main
            build_main()
            return True
        except Exception as e:
            print(f"Warning: Failed to build rust-analyzer: {e}")
            print("You can build it manually later with: python build_rust.py")
            print("Or download pre-built binaries from the GitHub releases.")
            return False


class CustomBuildPy(build_py, PlatformBinaryHandler):
    """Custom build command that handles platform-specific binaries"""
    
    def run(self):
        self.setup_platform_binary()
        super().run()


class CustomDevelop(develop, PlatformBinaryHandler):
    """Custom develop command that handles platform-specific binaries"""
    
    def run(self):
        self.setup_platform_binary()
        super().run()


class CustomInstall(install, PlatformBinaryHandler):
    """Custom install command that handles platform-specific binaries"""
    
    def run(self):
        self.setup_platform_binary()
        super().run()


# Determine package data based on available binaries
def get_package_data():
    """Get package data including all available binaries"""
    package_data = {
        'solana_fcg_tool': ['output/*', '*.md'],
    }
    
    bin_dir = Path("solana_fcg_tool") / "bin"
    if bin_dir.exists():
        # Include all binary files
        binary_files = []
        for file in bin_dir.iterdir():
            if file.is_file():
                binary_files.append(f"bin/{file.name}")
        
        if binary_files:
            package_data['solana_fcg_tool'].extend(binary_files)
    
    return package_data


setup(
    name="solana-fcg-tool",
    version="1.0.5",
    description="A Rust project analyzer for Solana development with multi-platform support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/solana-fcg-tool",
    packages=find_packages(include=['solana_fcg_tool', 'solana_fcg_tool.*']),
    python_requires=">=3.7",
    install_requires=[],
    include_package_data=True,
    package_data=get_package_data(),
    entry_points={
        'console_scripts': [
            'solana-fcg-tool=solana_fcg_tool.cli:main',
        ],
    },
    cmdclass={
        'build_py': CustomBuildPy,
        'develop': CustomDevelop,
        'install': CustomInstall,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Rust",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Code Generators",
    ],
    keywords="solana rust analyzer static-analysis call-graph",
    zip_safe=False,
)