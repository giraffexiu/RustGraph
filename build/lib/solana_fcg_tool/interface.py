#!/usr/bin/env python3
"""
Solana Analyzer Interface
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any


class SolanaAnalyzer:
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        # Try to find rust-analyzer binary in multiple locations
        self.rust_analyzer_path = self._find_rust_analyzer_binary()
    
    def find_symbols(self, symbol_name: str):
        """Find symbols in the project using source-finder"""
        if not self._validate_project():
            return {"error": "Invalid Rust project path"}
        
        if not symbol_name:
            return {"error": "Symbol name is required"}
        
        try:
            self._ensure_rust_analyzer_built()
            
            cmd = [
                str(self.rust_analyzer_path),
                "source-finder",
                symbol_name,
                str(self.project_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return {"error": f"Source search failed: {result.stderr}"}
            
            # Return the raw output directly as source_finder.rs outputs it
            output_text = result.stdout.strip()
            if not output_text:
                return {"error": "No output received"}
            
            # source_finder.rs outputs each symbol as a separate JSON object, one per line
            # We need to return the raw text output as-is to match exactly
            return output_text
            
        except Exception as e:
            return {"error": f"Error during source search: {e}"}
    
    def analyze_structs(self) -> Dict[str, Any]:
        """Analyze structs in the project"""
        if not self._validate_project():
            return {"error": "Invalid Rust project path"}
        
        try:
            # Import and use struct analyzer
            import sys
            sys.path.insert(0, str(Path(__file__).parent))
            
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "struct_analyzer", 
                Path(__file__).parent / "struct-anayzer.py"
            )
            struct_analyzer_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(struct_analyzer_module)
            
            extractor = struct_analyzer_module.SolanaStructExtractor(str(self.project_path))
            extractor.extract_from_project()
            
            return {
                "structs_count": len(extractor.structs),
                "constants_count": len(extractor.constants),
                "program_ids_count": len(extractor.program_ids),
                "summary": f"Found {len(extractor.structs)} structs, {len(extractor.constants)} constants, {len(extractor.program_ids)} program IDs"
            }
            
        except Exception as e:
            return {"error": f"Error during struct analysis: {e}"}
    
    def analyze_call_graph(self) -> Dict[str, Any]:
        """Analyze call graph in the project"""
        if not self._validate_project():
            return {"error": "Invalid Rust project path"}
        
        try:
            self._ensure_rust_analyzer_built()
            
            # Create temporary file for output
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_output_path = temp_file.name
            
            try:
                # Run rust-analyzer function analyzer
                cmd = [
                    str(self.rust_analyzer_path),
                    "function-analyzer",
                    str(self.project_path.resolve()),
                    "--output", temp_output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode != 0:
                    return {"error": f"Call graph analysis failed: {result.stderr}"}
                
                # Run JSON analyzer
                json_output = self._run_json_analyzer(temp_output_path)
                return json_output if json_output else {"error": "JSON analysis failed"}
                
            finally:
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
            
        except Exception as e:
            return {"error": f"Error during call graph analysis: {e}"}
    
    def save_results(self, data: Dict[str, Any], output_path: str) -> bool:
        """Save analysis results to JSON file"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Results saved to: {output_path}")
            return True
        except Exception as e:
            print(f"Failed to save results: {e}")
            return False
    
    def _validate_project(self) -> bool:
        """Validate if the path is a valid Rust project"""
        if not self.project_path.exists():
            return False
        
        cargo_toml = self.project_path / "Cargo.toml"
        return cargo_toml.exists()
    
    def _find_rust_analyzer_binary(self) -> Path:
        """Find rust-analyzer binary in multiple possible locations"""
        # Possible locations for rust-analyzer binary
        possible_paths = [
            # 1. In the same directory as this package (for development)
            Path(__file__).parent.parent / "target" / "release" / "rust-analyzer",
            # 2. In package data directory (for installed package)
            Path(__file__).parent / "bin" / "rust-analyzer",
            # 3. In system PATH
            Path("rust-analyzer"),  # Will be resolved by subprocess
            # 4. Relative to package root
            Path(__file__).parent.parent / "rust-analyzer",
        ]
        
        for path in possible_paths:
            if path.name == "rust-analyzer" and path.parent.name in ["bin", "release"]:
                if path.exists():
                    return path
            elif path.name == "rust-analyzer":
                # For system PATH, we'll try it in subprocess
                try:
                    result = subprocess.run(["which", "rust-analyzer"], capture_output=True, text=True)
                    if result.returncode == 0:
                        return Path(result.stdout.strip())
                except:
                    continue
        
        # Default to the development location
        return Path(__file__).parent.parent / "target" / "release" / "rust-analyzer"
    
    def _ensure_rust_analyzer_built(self):
        """Ensure rust-analyzer binary is built"""
        if not self.rust_analyzer_path.exists():
            print("Building rust-analyzer...")
            # Try to find the project root for building
            project_root = self._find_project_root()
            build_cmd = ["cargo", "build", "--release"]
            build_result = subprocess.run(
                build_cmd,
                cwd=project_root,
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                raise Exception(f"Failed to build rust-analyzer: {build_result.stderr}")
    
    def _find_project_root(self) -> Path:
        """Find the project root directory containing Cargo.toml"""
        current = Path(__file__).parent
        while current != current.parent:
            if (current / "Cargo.toml").exists():
                return current
            current = current.parent
        
        # Fallback to parent directory
        return Path(__file__).parent.parent
    

    def _run_json_analyzer(self, input_file: str) -> Optional[Dict[str, Any]]:
        """Run JSON analyzer on function analysis output."""
        try:
            import sys
            analyzer_script = Path(__file__).parent / "funcation-anayzer.py"
            project_name = self.project_path.name
            input_abs = str(Path(input_file).resolve())
            cmd = [sys.executable, str(analyzer_script), input_abs, project_name]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if result.returncode != 0:
                return None
            
            # Find output file
            output_lines = result.stdout.strip().split('\n')
            for line in output_lines:
                if "Results saved to:" in line:
                    json_path = line.split("Results saved to:")[1].strip()
                    if os.path.exists(json_path):
                        with open(json_path, 'r', encoding='utf-8') as f:
                            return json.load(f)
            
            return None
            
        except Exception:
            return None


# Convenience functions
def find_symbols(project_path: str, symbol_name: str):
    """Find symbols in a Rust project"""
    analyzer = SolanaAnalyzer(project_path)
    return analyzer.find_symbols(symbol_name)


def analyze_structs(project_path: str) -> Dict[str, Any]:
    """Analyze structs in a Rust project"""
    analyzer = SolanaAnalyzer(project_path)
    return analyzer.analyze_structs()


def analyze_call_graph(project_path: str) -> Dict[str, Any]:
    """Analyze call graph in a Rust project"""
    analyzer = SolanaAnalyzer(project_path)
    return analyzer.analyze_call_graph()