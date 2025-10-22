#!/usr/bin/env python3
"""
Solana Analyzer - A comprehensive Rust project analyzer for Solana development

This package provides tools for analyzing Rust projects, specifically designed
for Solana blockchain development. It includes functionality for:

- Source code symbol finding
- Struct and constant analysis  
- Call graph generation
- Function dependency analysis

Main Classes:
    SolanaAnalyzer: Main analyzer class for project analysis

Main Functions:
    find_symbols: Find symbols in a Rust project
    analyze_structs: Analyze structs and constants in a project
    analyze_call_graph: Generate call graph for a project

Example:
    >>> from solana_analyzer import SolanaAnalyzer
    >>> analyzer = SolanaAnalyzer("/path/to/rust/project")
    >>> result = analyzer.find_symbols("my_function")
    >>> print(result)
    
    Or using convenience functions:
    >>> from solana_analyzer import find_symbols, analyze_structs
    >>> symbols = find_symbols("/path/to/project", "my_function")
    >>> structs = analyze_structs("/path/to/project")
"""

__version__ = "1.0.0"
__author__ = "Solana Analyzer Team"
__email__ = ""

# Import main classes and functions
from .interface import (
    SolanaAnalyzer,
    find_symbols,
    analyze_structs,
    analyze_call_graph
)

# Import CLI for programmatic access
from . import cli

# Define what gets imported with "from solana_analyzer import *"
__all__ = [
    'SolanaAnalyzer',
    'find_symbols', 
    'analyze_structs',
    'analyze_call_graph',
    'cli'
]

# Package metadata
__title__ = "solana-analyzer"
__description__ = "A comprehensive Rust project analyzer for Solana development"
__url__ = "https://github.com/your-repo/solana-analyzer"
__license__ = "MIT"