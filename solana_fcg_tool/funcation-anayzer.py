#!/usr/bin/env python3
"""
Call Graph Analyzer

Integrates Rust call hierarchy analysis with JSON output generation.
"""

import re
import json
import os
import sys
import subprocess
import tempfile
from typing import Dict, List
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path

@dataclass
class Function:
    """Function information"""
    file_path: str
    line: int
    name: str
    call_count: int = 0
    calls: List[str] = None
    
    def __post_init__(self):
        if self.calls is None:
            self.calls = []
    
    def get_id(self) -> str:
        return f"{self.file_path}:{self.line}:{self.name}"

class CallGraphAnalyzer:
    """Call graph analyzer for JSON output"""
    
    def __init__(self):
        self.functions: Dict[str, Function] = {}
    
    def parse_file(self, file_path: str) -> None:
        """Parse call relationship file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ' -> ' in line:
                    self._parse_call_line(line)
    
    def _parse_call_line(self, line: str) -> None:
        """Parse single call relationship line"""
        pattern = r'^(.+?)\s*->\s*(.+?)\s*\(call at (\d+):(\d+)\)$'
        match = re.match(pattern, line)
        
        if not match:
            return
        
        caller_str, callee_str, _, _ = match.groups()
        
        caller = self._parse_function_info(caller_str.strip())
        callee = self._parse_function_info(callee_str.strip())
        
        if caller and callee:
            self._add_call_relationship(caller, callee)
    
    def _parse_function_info(self, func_str: str) -> Function:
        """Parse function information string"""
        pattern = r'^(.+?):(\d+):(.+)$'
        match = re.match(pattern, func_str)
        
        if not match:
            return None
        
        file_path, line, name = match.groups()
        return Function(file_path, int(line), name)
    
    def _add_call_relationship(self, caller: Function, callee: Function) -> None:
        """Add call relationship to graph"""
        caller_id = caller.get_id()
        callee_id = callee.get_id()
        
        if caller_id not in self.functions:
            self.functions[caller_id] = caller
        if callee_id not in self.functions:
            self.functions[callee_id] = callee
        
        self.functions[caller_id].call_count += 1
        self.functions[caller_id].calls.append(callee_id)
        
        # Graph structure is implicit in the 'calls' list; no external deps required
    
    def to_json(self) -> str:
        """Convert call graph to JSON format"""
        functions_dict = {}
        for func_id, func in self.functions.items():
            functions_dict[func_id] = {
                'file_path': func.file_path,
                'line': func.line,
                'name': func.name,
                'call_count': func.call_count,
                'calls': func.calls
            }
        
        result = {
            'functions': functions_dict
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)

def run_rust_analyzer(project_path: str, output_file: str) -> bool:
    """Run rust-analyzer call hierarchy analysis"""
    try:
        rust_analyzer_dir = Path(__file__).parent.parent
        
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
        
        print(f"Analyzing project: {project_path}")
        binary_path = rust_analyzer_dir / "target" / "release" / "rust-analyzer"
        
        if not binary_path.exists():
            print(f"Error: rust-analyzer binary not found at {binary_path}")
            return False
        
        analysis_cmd = [
            str(binary_path),
            "function-analyzer",
            str(Path(project_path).resolve()),
            "--output", output_file
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

def run_json_analyzer(input_file: str, project_name: str = None) -> str:
    """Run JSON analyzer on call hierarchy output"""
    try:
        if project_name is None:
            input_basename = os.path.basename(input_file)
            project_name = os.path.splitext(input_basename)[0]
        
        script_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(script_dir, "output")
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, f"{project_name}_call_graph.json")
        
        analyzer = CallGraphAnalyzer()
        analyzer.parse_file(input_file)
        json_result = analyzer.to_json()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_result)
        
        print(f"Analysis complete. Results saved to: {output_file}")
        print(f"Total functions: {len(analyzer.functions)}")
        
        return output_file
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def analyze_project(project_path: str) -> str:
    """Complete project analysis pipeline"""
    if not os.path.exists(project_path):
        print(f"Error: Project path '{project_path}' does not exist.")
        return None
    
    cargo_toml = os.path.join(project_path, "Cargo.toml")
    if not os.path.exists(cargo_toml):
        print(f"Error: '{project_path}' does not appear to be a Rust project (no Cargo.toml found).")
        return None
    
    print(f"Starting analysis of Rust project: {project_path}")
    print("=" * 60)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_output_path = temp_file.name
    
    try:
        success = run_rust_analyzer(project_path, temp_output_path)
        if not success:
            print("Failed to complete rust-analyzer analysis.")
            return None
        
        project_name = os.path.basename(project_path)
        json_output_path = run_json_analyzer(temp_output_path, project_name)
        if not json_output_path:
            print("Failed to generate JSON analysis.")
            return None
        
        print("=" * 60)
        print(f"Analysis pipeline completed successfully!")
        print(f"Final JSON output: {json_output_path}")
        
        if os.path.exists(json_output_path):
            with open(json_output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                function_count = len(data.get('functions', {}))
                print(f"Total functions analyzed: {function_count}")
        
        return json_output_path
        
    finally:
        if os.path.exists(temp_output_path):
            os.unlink(temp_output_path)

def main():
    """Main function for both project analysis and JSON processing"""
    if len(sys.argv) < 2:
        print("Usage:")
        print("  Project analysis: python funcation-anayzer.py <project_path>")
        print("  JSON processing:  python funcation-anayzer.py <input_file> [project_name]")
        print()
        print("Examples:")
        print("  python funcation-anayzer.py /path/to/rust/project")
        print("  python funcation-anayzer.py ../temp_file.txt mango-v3")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    if os.path.isdir(input_path):
        result = analyze_project(input_path)
        if not result:
            sys.exit(1)
    else:
        project_name = sys.argv[2] if len(sys.argv) > 2 else None
        result = run_json_analyzer(input_path, project_name)
        if not result:
            sys.exit(1)

if __name__ == '__main__':
    main()