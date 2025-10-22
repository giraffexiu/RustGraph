#!/usr/bin/env python3
"""
Solana Analyzer CLI

Command line interface for Rust project analysis.
"""

import sys
import argparse
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from interface import SolanaAnalyzer


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


def run_source_finder(args):
    """Run source finder analysis"""
    analyzer = SolanaAnalyzer(args.project_path)
    result = analyzer.find_symbols(args.symbol_name)
    
    # Check if result is an error dictionary
    if isinstance(result, dict) and "error" in result:
        print(f"✗ Source finder failed: {result['error']}")
        return False
    else:
        # result is the raw JSON output from source_finder.rs, print it directly
        print(result)
        return True


def run_struct_analyzer(args):
    """Run struct analyzer"""
    analyzer = SolanaAnalyzer(args.project_path)
    result = analyzer.analyze_structs()
    
    if "error" in result:
        print(f"✗ Struct analysis failed: {result['error']}")
        return False
    else:
        print("✓ Struct analysis completed")
        print(f"  Project: {args.project_path}")
        print(f"  {result.get('summary', 'Analysis completed')}")
        return True


def run_call_graph_analyzer(args):
    """Run call graph analyzer"""
    analyzer = SolanaAnalyzer(args.project_path)
    result = analyzer.analyze_call_graph()
    
    if "error" in result:
        print(f"✗ Call graph analysis failed: {result['error']}")
        return False
    else:
        print("✓ Call graph analysis completed")
        print(f"  Project: {args.project_path}")
        
        # Try to find and display output file info
        output_dir = Path(__file__).parent / "output"
        if output_dir.exists():
            json_files = list(output_dir.glob("*_call_graph.json"))
            if json_files:
                latest_file = max(json_files, key=lambda f: f.stat().st_mtime)
                print(f"  Output: {latest_file}")
        
        return True


def main():
    """Main function"""
    parser = create_parser()
    args = parser.parse_args()
    
    if not validate_args(args):
        sys.exit(1)
    
    success = False
    
    if args.analyzer_type == "source-finder":
        success = run_source_finder(args)
    elif args.analyzer_type == "struct-analyzer":
        success = run_struct_analyzer(args)
    elif args.analyzer_type == "call-graph":
        success = run_call_graph_analyzer(args)
    else:
        print(f"Error: Unknown analyzer type: {args.analyzer_type}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()