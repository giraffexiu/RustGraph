"""
Rust Call Graph Analyzer Library

A Python library for analyzing Rust project call hierarchies and generating JSON output.
"""

from .analyzer import RustCallGraphAnalyzer, analyze_project

__version__ = "1.0.0"
__author__ = "RustGraph Team"

__all__ = [
    "RustCallGraphAnalyzer",
    "analyze_project"
]