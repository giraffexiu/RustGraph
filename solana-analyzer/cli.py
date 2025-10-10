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
  # Source finder
  python cli.py source-finder my_function /path/to/project
  
  # Struct analyzer
  python cli.py struct-analyzer /path/to/project
  
  # Call graph analyzer
  python cli.py call-graph /path/to/project
        """
    )
    
    # Global options
    # No global options needed
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="analyzer_type", help="Analyzer type", required=True)
    
    # Source finder
    source_parser = subparsers.add_parser("source-finder", help="Source finder analyzer")
    source_parser.add_argument("symbol_name", help="Symbol name")
    source_parser.add_argument("project_path", help="Rust project path")
    
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
        "source-finder": AnalyzerType.SOURCE_FINDER,
        "struct-analyzer": AnalyzerType.STRUCT_ANALYZER,
        "call-graph": AnalyzerType.CALL_GRAPH
    }
    
    analyzer_type = analyzer_type_map[args.analyzer_type]
    
    config = AnalysisConfig(
        project_path=args.project_path,
        analyzer_type=analyzer_type,
        output_format=OutputFormat.JSON,
        output_path=None,
        output_base_dir=str(Path(__file__).parent / "output")
    )
    
    # Source finder specific config
    if analyzer_type == AnalyzerType.SOURCE_FINDER:
        config.symbol_name = args.symbol_name
    
    return config


def print_result_summary(result):
    """Print result summary"""
    if result.success:
        # For source finder, output results directly without any additional info
        if result.analyzer_type == AnalyzerType.SOURCE_FINDER and result.data:
            source_code = result.data.get("source_code", "")
            if source_code:
                print(source_code)
            else:
                print("No source code found")
        else:
            print("✓ Analysis completed")
            print(f"  Analyzer: {result.analyzer_type.value}")
            print(f"  Project: {result.config.project_path}")
            
            if result.execution_time:
                print(f"  Time: {result.execution_time:.2f}s")
            
            if result.output_path:
                print(f"  Output: {result.output_path}")
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
    
    analyzer = RustProjectAnalyzer()
    result = analyzer.analyze(config)
    
    print_result_summary(result)
    
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()