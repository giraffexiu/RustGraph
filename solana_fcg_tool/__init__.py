"""
solana_fcg_tool package public API.

This module exposes the primary classes and convenience functions for consumers:

    from solana_fcg_tool import SolanaAnalyzer
    from solana_fcg_tool import find_symbols, analyze_structs, analyze_call_graph
"""

from .interface import (
    SolanaAnalyzer,
    find_symbols,
    analyze_structs,
    analyze_call_graph,
)

__title__ = "solana-fcg-tool"
__description__ = "A comprehensive Rust project analyzer for Solana development"
__version__ = "1.0.3"

__all__ = [
    "SolanaAnalyzer",
    "find_symbols",
    "analyze_structs",
    "analyze_call_graph",
]