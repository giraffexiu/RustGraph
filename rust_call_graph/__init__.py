"""
Rust Call Graph Analyzer Library

A Python library for analyzing Rust project call hierarchies and generating JSON output.
"""

from .analyzer import RustCallGraphAnalyzer, analyze_project, analyze_anchor_structs, AnalysisResult, StructAnalysisResult

__version__ = "1.0.0"
__all__ = [
    "RustCallGraphAnalyzer",
    "analyze_project", 
    "analyze_anchor_structs",
    "AnalysisResult",
    "StructAnalysisResult"
]