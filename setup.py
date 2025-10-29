#!/usr/bin/env python3
"""
Setup script for Solana Analyzer package
"""

import os
import sys
from setuptools import setup, find_packages
from setuptools.command.build_py import build_py
from setuptools.command.develop import develop
from setuptools.command.install import install
from pathlib import Path

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""


class BuildRustCommand:
    """Mixin class to add rust-analyzer building functionality"""
    
    def build_rust_analyzer(self):
        """Build the rust-analyzer binary"""
        print("Building custom rust-analyzer binary...")
        
        # Import and run the build script
        try:
            from build_rust import main as build_main
            build_main()
        except Exception as e:
            print(f"Warning: Failed to build rust-analyzer: {e}")
            print("You can build it manually later with: python build_rust.py")


class CustomBuildPy(build_py, BuildRustCommand):
    """Custom build command that builds rust-analyzer"""
    
    def run(self):
        self.build_rust_analyzer()
        super().run()


class CustomDevelop(develop, BuildRustCommand):
    """Custom develop command that builds rust-analyzer"""
    
    def run(self):
        self.build_rust_analyzer()
        super().run()


class CustomInstall(install, BuildRustCommand):
    """Custom install command that builds rust-analyzer"""
    
    def run(self):
        self.build_rust_analyzer()
        super().run()

setup(
    name="solana-fcg-tool",
    version="1.0.2",
    description="A Rust project analyzer for Solana development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include=['solana_fcg_tool', 'solana_fcg_tool.*']),
    python_requires=">=3.7",
    install_requires=[],
    include_package_data=True,
    package_data={
        'solana_fcg_tool': ['bin/*', 'output/*', '*.md'],
    },
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
    zip_safe=False,
)