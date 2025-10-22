#!/usr/bin/env python3
"""
Setup script for Solana Analyzer package
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8') if (this_directory / "README.md").exists() else ""

setup(
    name="solana-analyzer",
    version="0.1.0",
    description="A Rust project analyzer for Solana development",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include=['solana_analyzer', 'solana_analyzer.*']),
    python_requires=">=3.7",
    install_requires=[],
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'solana-analyzer=solana_analyzer.cli:main',
        ],
    },
    zip_safe=False,
)