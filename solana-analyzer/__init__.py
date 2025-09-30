"""
Solana Analyzer Library

Unified Rust project analysis library with symbol finder, struct analyzer, and call graph analyzer.
"""

from .interface import (
    # Core classes
    RustProjectAnalyzer,
    AnalysisConfig,
    AnalysisResult,
    
    # Enums
    AnalyzerType,
    OutputFormat,
    
    # Output handlers
    OutputHandler,
    FileOutputHandler,
    CallbackOutputHandler,
    
    # Analyzers
    BaseAnalyzer,
    SymbolFinderAnalyzer,
    StructAnalyzer,
    CallGraphAnalyzer,
    AnalyzerFactory,
    
    # Convenience functions
    analyze_symbols,
    analyze_structs,
    analyze_call_graph,
)

# Version info
__version__ = "1.0.0"
__author__ = "Solana Analyzer Team"
__description__ = "Unified Rust project analysis library"

# Public interface
__all__ = [
    # Core classes
    "RustProjectAnalyzer",
    "AnalysisConfig", 
    "AnalysisResult",
    
    # Enums
    "AnalyzerType",
    "OutputFormat",
    
    # Output handlers
    "OutputHandler",
    "FileOutputHandler", 
    "CallbackOutputHandler",
    
    # Analyzers
    "BaseAnalyzer",
    "SymbolFinderAnalyzer",
    "StructAnalyzer",
    "CallGraphAnalyzer",
    "AnalyzerFactory",
    
    # Convenience functions
    "analyze_symbols",
    "analyze_structs", 
    "analyze_call_graph",
    
    # Meta info
    "__version__",
    "__author__",
    "__description__",
]