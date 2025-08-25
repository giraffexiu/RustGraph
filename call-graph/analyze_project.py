#!/usr/bin/env python3
"""
Project Call Hierarchy Analyzer

This script integrates the Rust call hierarchy analysis with JSON output generation.
It takes a project path as input and produces a JSON file with call relationship analysis.
"""

import os
import sys
import subprocess
import tempfile
from pathlib import Path

def run_rust_analyzer(project_path: str, output_file: str) -> bool:
    """
    Run rust-analyzer call hierarchy analysis
    
    Args:
        project_path: Path to the Rust project to analyze
        output_file: Path to save the call hierarchy output
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Get the rust-analyzer binary path
        rust_analyzer_dir = Path(__file__).parent.parent
        
        # Build rust-analyzer if needed
        print("Building rust-analyzer...")
        build_cmd = ["cargo", "build", "--release"]
        build_result = subprocess.run(
            build_cmd, 
            cwd=rust_analyzer_dir, 
            capture_output=True, 
            text=True
        )
        
        if build_result.returncode != 0:
            print(f"Failed to build rust-analyzer: {build_result.stderr}")
            return False
        
        # Run call hierarchy analysis
        print(f"Analyzing project: {project_path}")
        binary_path = rust_analyzer_dir / "target" / "release" / "rust-analyzer"
        
        analysis_cmd = [
            str(binary_path),
            "call-hierarchy",
            "--path", project_path,
            "--output", output_file,
            "--filter-external"  # Filter external dependencies
        ]
        
        analysis_result = subprocess.run(
            analysis_cmd,
            capture_output=True,
            text=True
        )
        
        if analysis_result.returncode != 0:
            print(f"Call hierarchy analysis failed: {analysis_result.stderr}")
            return False
        
        print("Call hierarchy analysis completed successfully")
        return True
        
    except Exception as e:
        print(f"Error running rust-analyzer: {e}")
        return False

def run_json_analyzer(input_file: str) -> str:
    """
    Run the Python JSON analyzer
    
    Args:
        input_file: Path to the call hierarchy output file
    
    Returns:
        Path to the generated JSON file, or None if failed
    """
    try:
        # Get the json_processor.py path
        analyzer_script = Path(__file__).parent / "json_processor.py"
        
        print(f"Generating JSON analysis from: {input_file}")
        
        # Run the JSON analyzer
        json_cmd = [sys.executable, str(analyzer_script), input_file]
        json_result = subprocess.run(
            json_cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if json_result.returncode != 0:
            print(f"JSON analysis failed: {json_result.stderr}")
            return None
        
        print(json_result.stdout)
        
        # Extract output file path from the analyzer output
        # The analyzer prints: "Analysis complete. Results saved to: <path>"
        output_lines = json_result.stdout.strip().split('\n')
        for line in output_lines:
            if "Results saved to:" in line:
                json_file_path = line.split("Results saved to:")[1].strip()
                return json_file_path
        
        # Fallback: construct expected path
        input_basename = os.path.basename(input_file)
        input_name, _ = os.path.splitext(input_basename)
        output_dir = Path(__file__).parent / "output"
        expected_json_path = output_dir / f"{input_name}_call_graph.json"
        
        if expected_json_path.exists():
            return str(expected_json_path)
        
        return None
        
    except Exception as e:
        print(f"Error running JSON analyzer: {e}")
        return None

def main():
    """
    Main function to orchestrate the analysis pipeline
    """
    if len(sys.argv) != 2:
        print("Usage: python analyze_project.py <project_path>")
        print("Example: python analyze_project.py /path/to/rust/project")
        sys.exit(1)
    
    project_path = sys.argv[1]
    
    # Validate project path
    if not os.path.exists(project_path):
        print(f"Error: Project path '{project_path}' does not exist.")
        sys.exit(1)
    
    # Check if it's a Rust project (has Cargo.toml)
    cargo_toml = os.path.join(project_path, "Cargo.toml")
    if not os.path.exists(cargo_toml):
        print(f"Error: '{project_path}' does not appear to be a Rust project (no Cargo.toml found).")
        sys.exit(1)
    
    print(f"Starting analysis of Rust project: {project_path}")
    print("=" * 60)
    
    # Step 1: Run rust-analyzer call hierarchy analysis
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_output_path = temp_file.name
    
    try:
        success = run_rust_analyzer(project_path, temp_output_path)
        if not success:
            print("Failed to complete rust-analyzer analysis.")
            sys.exit(1)
        
        # Step 2: Run JSON analysis
        json_output_path = run_json_analyzer(temp_output_path)
        if not json_output_path:
            print("Failed to generate JSON analysis.")
            sys.exit(1)
        
        print("=" * 60)
        print(f"Analysis pipeline completed successfully!")
        print(f"Final JSON output: {json_output_path}")
        
        # Show some basic statistics
        if os.path.exists(json_output_path):
            import json
            with open(json_output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                function_count = len(data.get('functions', {}))
                print(f"Total functions analyzed: {function_count}")
        
    finally:
        # Clean up temporary file
        if os.path.exists(temp_output_path):
            os.unlink(temp_output_path)

if __name__ == '__main__':
    main()