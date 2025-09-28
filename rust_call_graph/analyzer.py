"""
Rust Call Graph Analyzer

Main analyzer module that provides a clean interface for analyzing Rust projects.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class AnalysisResult:
    """Analysis result container"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    output_file: Optional[str] = None
    function_count: int = 0


@dataclass
class StructAnalysisResult:
    """Struct analysis result container"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    output_file: Optional[str] = None
    struct_count: int = 0
    anchor_struct_count: int = 0
    pda_count: int = 0


class RustCallGraphAnalyzer:
    """
    Main analyzer class for Rust call graph analysis
    """
    
    def __init__(self, rust_analyzer_path: Optional[str] = None):
        """
        Initialize the analyzer
        
        Args:
            rust_analyzer_path: Optional path to rust-analyzer binary
        """
        self._call_graph_dir = None
        self._rust_analyzer_path = rust_analyzer_path
    
    def _get_call_graph_dir(self) -> Path:
        """Get the call-graph directory"""
        if self._call_graph_dir is None:
            current_dir = Path(__file__).parent.parent
            self._call_graph_dir = current_dir / "call-graph"
        return self._call_graph_dir
    
    def _get_rust_analyzer_binary(self) -> Path:
        """Get the rust-analyzer binary path"""
        if self._rust_analyzer_path:
            return Path(self._rust_analyzer_path)
        
        # Default to the built binary in the project
        current_dir = Path(__file__).parent.parent
        binary_path = current_dir / "target" / "release" / "rust-analyzer"
        
        if not binary_path.exists():
            # Try debug build
            binary_path = current_dir / "target" / "debug" / "rust-analyzer"
        
        return binary_path
    
    def analyze(self, project_path: str, output_dir: Optional[str] = None, 
                project_name: Optional[str] = None) -> AnalysisResult:
        """
        Analyze a Rust project and generate call graph JSON
        
        Args:
            project_path: Path to the Rust project to analyze
            output_dir: Optional output directory. If None, uses call-graph/output.
            project_name: Optional project name for output file. If None, uses directory name.
        
        Returns:
            AnalysisResult containing the analysis results
        """
        try:
            # Validate project path
            if not os.path.exists(project_path):
                return AnalysisResult(
                    success=False,
                    error=f"Project path '{project_path}' does not exist."
                )
            
            # Check if it's a Rust project
            cargo_toml = os.path.join(project_path, "Cargo.toml")
            if not os.path.exists(cargo_toml):
                return AnalysisResult(
                    success=False,
                    error=f"'{project_path}' does not appear to be a Rust project (no Cargo.toml found)."
                )
            
            # Determine project name
            if project_name is None:
                project_name = os.path.basename(os.path.abspath(project_path))
            
            # Use existing call-graph script
            call_graph_dir = self._get_call_graph_dir()
            analyze_script = call_graph_dir / "analyze_project.py"
            
            if not analyze_script.exists():
                return AnalysisResult(
                    success=False,
                    error=f"analyze_project.py not found at {analyze_script}"
                )
            
            print(f"Running analysis for project: {project_path}")
            
            # Run the existing analyze_project.py script
            analysis_cmd = [sys.executable, str(analyze_script), project_path]
            analysis_result = subprocess.run(
                analysis_cmd,
                capture_output=True,
                text=True,
                cwd=call_graph_dir
            )
            
            if analysis_result.returncode != 0:
                return AnalysisResult(
                    success=False,
                    error=f"Analysis failed: {analysis_result.stderr}"
                )
            
            # Find the generated JSON file
            output_dir_path = call_graph_dir / "output"
            json_file_pattern = f"{project_name}_call_graph.json"
            json_output_path = output_dir_path / json_file_pattern
            
            if not json_output_path.exists():
                # Try to find any JSON file in output directory
                json_files = list(output_dir_path.glob("*_call_graph.json"))
                if json_files:
                    json_output_path = json_files[-1]  # Use the most recent one
                else:
                    return AnalysisResult(
                        success=False,
                        error=f"No JSON output file found in {output_dir_path}"
                    )
            
            # Read the JSON data
            with open(json_output_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            function_count = len(json_data.get('functions', {}))
            
            # Copy to custom output directory if specified
            final_output_path = str(json_output_path)
            if output_dir and output_dir != str(output_dir_path):
                os.makedirs(output_dir, exist_ok=True)
                custom_output_path = os.path.join(output_dir, json_file_pattern)
                with open(custom_output_path, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                final_output_path = custom_output_path
            
            return AnalysisResult(
                success=True,
                data=json_data,
                output_file=final_output_path,
                function_count=function_count
            )
                
        except Exception as e:
            return AnalysisResult(
                success=False,
                error=f"Analysis failed: {str(e)}"
            )
    
    def analyze_structs(self, project_path: str, project_name: Optional[str] = None) -> StructAnalysisResult:
        """
        Analyze Solana Anchor structs in a Rust project with full analysis enabled
        
        Args:
            project_path: Path to the Rust project to analyze
            project_name: Optional project name for output file. If None, uses directory name.
        
        Returns:
            StructAnalysisResult containing the analysis results
        """
        try:
            # Validate project path
            if not os.path.exists(project_path):
                return StructAnalysisResult(
                    success=False,
                    error=f"Project path '{project_path}' does not exist."
                )
            
            # Check if it's a Rust project
            cargo_toml = os.path.join(project_path, "Cargo.toml")
            anchor_toml = os.path.join(project_path, "Anchor.toml")
            if not os.path.exists(cargo_toml) and not os.path.exists(anchor_toml):
                return StructAnalysisResult(
                    success=False,
                    error=f"'{project_path}' does not appear to be a Rust/Anchor project (no Cargo.toml or Anchor.toml found)."
                )
            
            # Determine project name
            if project_name is None:
                project_name = os.path.basename(os.path.abspath(project_path))
            
            # Get rust-analyzer binary
            rust_analyzer_binary = self._get_rust_analyzer_binary()
            
            if not rust_analyzer_binary.exists():
                return StructAnalysisResult(
                    success=False,
                    error=f"rust-analyzer binary not found at {rust_analyzer_binary}. Please build the project first."
                )
            
            print(f"Running comprehensive Anchor struct analysis for project: {project_path}")
            
            # Fixed output directory (call-graph/output)
            current_dir = Path(__file__).parent.parent
            output_dir = current_dir / "call-graph" / "output"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            output_file = output_dir / f"{project_name}_anchor_analysis.json"
            
            # Build simplified command (all features enabled by default)
            cmd = [
                str(rust_analyzer_binary),
                "struct-analyzer",
                project_path
            ]
            
            print(f"Running command: {' '.join(cmd)}")
            
            # Run struct analysis
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=os.path.dirname(rust_analyzer_binary)
            )
            
            if result.returncode != 0:
                return StructAnalysisResult(
                    success=False,
                    error=f"Struct analysis failed: {result.stderr}"
                )
            
            # Read the generated JSON file
            if not output_file.exists():
                return StructAnalysisResult(
                    success=False,
                    error=f"Output file not generated: {output_file}"
                )
            
            with open(output_file, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            # Extract statistics
            statistics = json_data.get('statistics', {})
            struct_count = statistics.get('total_structs', 0)
            anchor_struct_count = statistics.get('anchor_structs', 0)
            pda_count = statistics.get('pda_fields', 0)
            
            return StructAnalysisResult(
                success=True,
                data=json_data,
                output_file=str(output_file),
                struct_count=struct_count,
                anchor_struct_count=anchor_struct_count,
                pda_count=pda_count
            )
            
        except Exception as e:
            return StructAnalysisResult(
                success=False,
                error=f"Struct analysis failed: {str(e)}"
            )


def analyze_project(project_path: str, output_dir: Optional[str] = None, 
                   project_name: Optional[str] = None) -> AnalysisResult:
    """
    Convenience function to analyze a Rust project
    
    Args:
        project_path: Path to the Rust project to analyze
        output_dir: Optional output directory
        project_name: Optional project name for output file
    
    Returns:
        AnalysisResult containing the analysis results
    
    Example:
        >>> from rust_call_graph import analyze_project
        >>> result = analyze_project("/path/to/rust/project")
        >>> if result.success:
        ...     print(f"Analysis completed! Found {result.function_count} functions")
        ...     print(f"Output saved to: {result.output_file}")
        ... else:
        ...     print(f"Analysis failed: {result.error}")
    """
    analyzer = RustCallGraphAnalyzer()
    return analyzer.analyze(project_path, output_dir, project_name)


def analyze_anchor_structs(project_path: str, project_name: Optional[str] = None) -> StructAnalysisResult:
    """
    Convenience function to analyze Solana Anchor structs in a Rust project
    All analysis features are enabled by default for comprehensive results.
    
    Args:
        project_path: Path to the Rust project to analyze
        project_name: Optional project name for output file
    
    Returns:
        StructAnalysisResult containing the analysis results
    
    Example:
        >>> from rust_call_graph import analyze_anchor_structs
        >>> result = analyze_anchor_structs("/path/to/anchor/project")
        >>> if result.success:
        ...     print(f"Analysis completed! Found {result.anchor_struct_count} Anchor structs")
        ...     print(f"Found {result.pda_count} PDA fields")
        ...     print(f"Output saved to: {result.output_file}")
        ... else:
        ...     print(f"Analysis failed: {result.error}")
    """
    analyzer = RustCallGraphAnalyzer()
    return analyzer.analyze_structs(project_path, project_name)