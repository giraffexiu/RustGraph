#!/usr/bin/env python3
"""
Solana Analyzer CLI

Command line interface for Rust project analysis.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

from interface import (
    RustProjectAnalyzer, AnalysisConfig, AnalyzerType, OutputFormat,
    FileOutputHandler, CallbackOutputHandler
)


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Solana project analysis tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Symbol finder
  python cli.py symbol-finder function my_function /path/to/project
  
  # Struct analyzer
  python cli.py struct-analyzer /path/to/project
  
  # Call graph analyzer
  python cli.py call-graph /path/to/project
        """
    )
    
    # Global options
    parser.add_argument("--disable-build-scripts", action="store_true", help="Disable build scripts")
    parser.add_argument("--disable-proc-macros", action="store_true", help="Disable proc macros")
    parser.add_argument("--proc-macro-srv", type=str, help="Proc macro server path")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="analyzer_type", help="Analyzer type", required=True)
    
    # Symbol finder
    symbol_parser = subparsers.add_parser("symbol-finder", help="Symbol finder analyzer")
    symbol_parser.add_argument("symbol_type", choices=["function", "struct", "fn"], help="Symbol type")
    symbol_parser.add_argument("symbol_name", help="Symbol name")
    symbol_parser.add_argument("project_path", help="Rust project path")
    
    # Struct analyzer
    struct_parser = subparsers.add_parser("struct-analyzer", help="Struct analyzer")
    struct_parser.add_argument("project_path", help="Rust project path")
    
    # Call graph analyzer
    call_graph_parser = subparsers.add_parser("call-graph", help="Call graph analyzer")
    call_graph_parser.add_argument("project_path", help="Rust project path")
    
    return parser


def validate_args(args) -> bool:
    """Validate command line arguments"""
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"Error: Project path does not exist: {args.project_path}")
        return False
    
    cargo_toml = project_path / "Cargo.toml"
    if not cargo_toml.exists():
        print(f"Error: Not a Rust project (no Cargo.toml found): {args.project_path}")
        return False
    
    return True


def create_config_from_args(args) -> AnalysisConfig:
    """Create analysis config from command line arguments"""
    analyzer_type_map = {
        "symbol-finder": AnalyzerType.SYMBOL_FINDER,
        "struct-analyzer": AnalyzerType.STRUCT_ANALYZER,
        "call-graph": AnalyzerType.CALL_GRAPH
    }
    
    analyzer_type = analyzer_type_map[args.analyzer_type]
    
    config = AnalysisConfig(
        project_path=args.project_path,
        analyzer_type=analyzer_type,
        output_format=OutputFormat.JSON,
        output_path=None,
        output_base_dir=str(Path(__file__).parent / "output"),
        disable_build_scripts=args.disable_build_scripts,
        disable_proc_macros=args.disable_proc_macros,
        proc_macro_srv=args.proc_macro_srv
    )
    
    # Symbol finder specific config
    if analyzer_type == AnalyzerType.SYMBOL_FINDER:
        symbol_type = args.symbol_type
        if symbol_type == "fn":
            symbol_type = "function"
        
        config.symbol_type = symbol_type
        config.symbol_name = args.symbol_name
    
    return config


def print_result_summary(result, verbose: bool = False):
    """Print result summary"""
    if result.success:
        print("✓ Analysis completed")
        print(f"  Analyzer: {result.analyzer_type.value}")
        print(f"  Project: {result.config.project_path}")
        
        if result.execution_time:
            print(f"  Time: {result.execution_time:.2f}s")
        
        # For symbol finder, output results to console
        if result.analyzer_type == AnalyzerType.SYMBOL_FINDER and result.data:
            print("\nSymbol search results:")
            source_code = result.data.get("source_code", "")
            if source_code:
                print(source_code)
            else:
                print("No source code found")
        elif result.output_path:
            print(f"  Output: {result.output_path}")
        
        # Print statistics
        if result.data and verbose and result.analyzer_type != AnalyzerType.SYMBOL_FINDER:
            print("\nStatistics:")
            if result.analyzer_type == AnalyzerType.STRUCT_ANALYZER:
                print(f"  Structs: {result.data.get('structs_count', 0)}")
                print(f"  Constants: {result.data.get('constants_count', 0)}")
                print(f"  Program IDs: {result.data.get('program_ids_count', 0)}")
                print(f"  Oracle info: {result.data.get('oracle_infos_count', 0)}")
                print(f"  Liquidity pools: {result.data.get('liquidity_pools_count', 0)}")
                print(f"  Lending pools: {result.data.get('lending_pools_count', 0)}")
                print(f"  Vaults: {result.data.get('vaults_count', 0)}")
                print(f"  Governance: {result.data.get('governance_infos_count', 0)}")
            elif result.analyzer_type == AnalyzerType.CALL_GRAPH:
                functions_count = len(result.data.get("functions", {}))
                print(f"  Functions: {functions_count}")
    else:
        print("✗ Analysis failed")
        print(f"  Error: {result.error_message}")
        if result.execution_time:
            print(f"  Time: {result.execution_time:.2f}s")


def main():
    """Main function"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not validate_args(args):
        sys.exit(1)
    
    config = create_config_from_args(args)
    
    if args.verbose:
        print(f"Starting analysis: {config.project_path}")
        print(f"Analyzer: {config.analyzer_type.value}")
        print("=" * 60)
    
    analyzer = RustProjectAnalyzer()
    result = analyzer.analyze(config)
    
    if args.verbose:
        print("=" * 60)
    
    print_result_summary(result, args.verbose)
    
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()