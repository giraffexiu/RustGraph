#!/usr/bin/env python3
"""
Solana Analyzer Core Module

Core module for Rust project analysis with symbol finder, struct analyzer, and call graph analyzer.
"""

import os
import sys
import json
import subprocess
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from enum import Enum


class AnalyzerType(Enum):
    """Analyzer type enumeration"""
    SOURCE_FINDER = "source_finder"
    STRUCT_ANALYZER = "struct_analyzer"
    CALL_GRAPH = "call_graph"


class OutputFormat(Enum):
    """Output format enumeration"""
    JSON = "json"
    TEXT = "text"
    DICT = "dict"


@dataclass
class AnalysisConfig:
    """Analysis configuration"""
    project_path: str
    analyzer_type: AnalyzerType
    output_format: OutputFormat = OutputFormat.JSON
    output_path: Optional[str] = None
    
    # Source finder specific config
    symbol_name: Optional[str] = None
    
    # Output config
    auto_generate_output_path: bool = True
    output_base_dir: str = field(default_factory=lambda: str(Path(__file__).parent / "output"))


@dataclass
class AnalysisResult:
    """Analysis result"""
    success: bool
    analyzer_type: AnalyzerType
    config: AnalysisConfig
    data: Optional[Dict[str, Any]] = None
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


class OutputHandler(ABC):
    """Output handler abstract base class"""
    
    @abstractmethod
    def handle_output(self, result: AnalysisResult) -> bool:
        """Handle output result"""
        pass


class FileOutputHandler(OutputHandler):
    """File output handler"""
    
    def handle_output(self, result: AnalysisResult) -> bool:
        """Output result to file"""
        if not result.success or not result.data:
            return False
        
        try:
            output_path = result.output_path
            if not output_path:
                return False
            
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if result.config.output_format == OutputFormat.JSON:
                    json.dump(result.data, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(result.data))
            
            print(f"Results saved to: {output_path}")
            return True
            
        except Exception as e:
            print(f"Failed to save results: {e}")
            return False


class CallbackOutputHandler(OutputHandler):
    """Callback output handler for programmatic use"""
    
    def __init__(self, callback: Callable[[AnalysisResult], bool]):
        self.callback = callback
    
    def handle_output(self, result: AnalysisResult) -> bool:
        """Handle result through callback function"""
        return self.callback(result)


class BaseAnalyzer(ABC):
    """Base analyzer class"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.project_root = Path(__file__).parent.parent
    
    @abstractmethod
    def analyze(self) -> AnalysisResult:
        """Execute analysis"""
        pass
    
    def _validate_project_path(self) -> bool:
        """Validate project path"""
        project_path = Path(self.config.project_path)
        
        if not project_path.exists():
            return False
        
        cargo_toml = project_path / "Cargo.toml"
        if not cargo_toml.exists():
            return False
        
        return True
    
    def _generate_output_path(self, suffix: str) -> str:
        """Generate output file path"""
        if self.config.output_path:
            return self.config.output_path
        
        if not self.config.auto_generate_output_path:
            return None
        
        project_name = Path(self.config.project_path).name
        output_dir = Path(self.config.output_base_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.output_format == OutputFormat.JSON:
            filename = f"{project_name}_{suffix}.json"
        else:
            filename = f"{project_name}_{suffix}.txt"
        
        return str(output_dir / filename)


class SourceFinderAnalyzer(BaseAnalyzer):
    """Source finder analyzer"""
    
    def analyze(self) -> AnalysisResult:
        """Execute source finder analysis"""
        import time
        start_time = time.time()
        
        if not self._validate_project_path():
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.SOURCE_FINDER,
                config=self.config,
                error_message=f"Invalid project path: {self.config.project_path}"
            )
        
        if not self.config.symbol_name:
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.SOURCE_FINDER,
                config=self.config,
                error_message="Source finder requires symbol_name"
            )
        
        try:
            binary_path = self.project_root / "target" / "release" / "rust-analyzer"
            
            if not binary_path.exists():
                self._build_rust_analyzer()
            
            cmd = [
                str(binary_path),
                "source-finder",
                self.config.symbol_name,
                self.config.project_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return AnalysisResult(
                    success=False,
                    analyzer_type=AnalyzerType.SOURCE_FINDER,
                    config=self.config,
                    error_message=f"Source search failed: {result.stderr}",
                    execution_time=time.time() - start_time
                )
            
            # Parse the enhanced output format with call graph information
            output_text = result.stdout.strip() if result.stdout else ""
            data = self._parse_source_finder_output(output_text)
            
            return AnalysisResult(
                success=True,
                analyzer_type=AnalyzerType.SOURCE_FINDER,
                config=self.config,
                data=data,
                output_path=None,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.SOURCE_FINDER,
                config=self.config,
                error_message=f"Error during source search: {e}",
                execution_time=time.time() - start_time
            )
    
    def _build_rust_analyzer(self):
        """Build rust-analyzer"""
        print("Building rust-analyzer...")
        build_cmd = ["cargo", "build", "--release"]
        build_result = subprocess.run(
            build_cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        if build_result.returncode != 0:
            raise Exception(f"Failed to build rust-analyzer: {build_result.stderr}")
    
    def _parse_source_finder_output(self, output_text: str) -> Dict[str, Any]:
        """Parse the enhanced source finder output with call graph information"""
        if not output_text:
            return {}
        
        lines = output_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith("File Path:"):
                file_path = line.replace("File Path:", "").strip()
                
                # Extract contract name from file path
                contract_name = self._extract_contract_name(file_path)
                
                # Read start line and end line
                start_line = 1
                end_line = 1
                
                i += 1
                if i < len(lines) and lines[i].strip().startswith("Start Line:"):
                    start_line = int(lines[i].replace("Start Line:", "").strip())
                    i += 1
                
                if i < len(lines) and lines[i].strip().startswith("End Line:"):
                    end_line = int(lines[i].replace("End Line:", "").strip())
                    i += 1
                
                # Read source code
                source_code = ""
                function_calls = []
                
                if i < len(lines) and lines[i].strip() == "Source Code:":
                    i += 1
                    source_lines = []
                    
                    while i < len(lines):
                        line = lines[i]
                        if line.strip() == "Function Calls:" or line.strip().startswith("Function Calls:"):
                            break
                        if line.strip() == "" and i + 1 < len(lines) and lines[i + 1].strip().startswith("File Path:"):
                            break
                        source_lines.append(line)
                        i += 1
                    
                    source_code = '\n'.join(source_lines).strip()
                
                # Parse function calls
                if i < len(lines) and lines[i].strip().startswith("Function Calls:"):
                    line = lines[i].strip()
                    if "None" not in line:
                        i += 1
                        while i < len(lines):
                            line = lines[i].strip()
                            if line.startswith("->"):
                                call_info = line.replace("->", "").strip()
                                if ":" in call_info:
                                    parts = call_info.rsplit(":", 2)
                                    if len(parts) >= 3:
                                        call_file_path = parts[0]
                                        call_func_name = parts[2]
                                        call_module = self._extract_contract_name(call_file_path)
                                        
                                        function_calls.append({
                                            "file": call_file_path,
                                            "functiion": call_func_name,  # Keep the typo as requested
                                            "module": call_module
                                        })
                            elif line == "" and i + 1 < len(lines) and lines[i + 1].strip().startswith("File Path:"):
                                break
                            elif line.startswith("File Path:"):
                                i -= 1
                                break
                            i += 1
                
                # Extract function name and parameters from source code
                function_name, parameters, _, _ = self._extract_function_info(source_code)
                
                # Return the first found function in the specified format
                return {
                    "contract": contract_name,
                    "function": function_name,
                    "source": source_code,
                    "location": {
                        "file": file_path,
                        "start_line": start_line,
                        "end_line": end_line
                    },
                    "parameter": parameters,
                    "calls": function_calls
                }
            
            i += 1
        
        return {}
    
    def _extract_contract_name(self, file_path: str) -> str:
        """Extract contract name from file path"""
        import os
        filename = os.path.basename(file_path)
        name_without_ext = os.path.splitext(filename)[0]
        return name_without_ext
    
    def _extract_function_info(self, source_code: str, file_path: str = "") -> tuple:
        """Extract function name, parameters, start and end line from source code"""
        if not source_code:
            return "", [], 1, 1
        
        lines = source_code.split('\n')
        function_name = ""
        parameters = []
        start_line = 1
        end_line = len(lines)
        
        # Look for function definition
        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if stripped_line.startswith("fn ") or stripped_line.startswith("pub fn "):
                # Parse Rust function
                function_name, parameters = self._parse_rust_function(stripped_line)
                start_line = i + 1
                break
            elif "function " in stripped_line:
                # Parse Solidity-like function (if any)
                function_name, parameters = self._parse_solidity_function(stripped_line)
                start_line = i + 1
                break
        
        if not function_name:
            # Fallback: try to extract any identifier
            for line in lines:
                stripped_line = line.strip()
                if stripped_line and not stripped_line.startswith("//") and not stripped_line.startswith("/*"):
                    # Try to find function-like patterns
                    import re
                    match = re.search(r'(\w+)\s*\(', stripped_line)
                    if match:
                        function_name = match.group(1)
                        break
        
        # Calculate actual line numbers by finding the source code in the original file
        if file_path and source_code.strip():
            actual_start, actual_end = self._find_source_location_in_file(source_code, file_path)
            if actual_start > 0:
                start_line = actual_start
                end_line = actual_end
        
        return function_name, parameters, start_line, end_line
    
    def _find_source_location_in_file(self, source_code: str, file_path: str) -> tuple:
        """Find the actual start and end line numbers of source code in the original file"""
        try:
            # Read the original file
            with open(file_path, 'r', encoding='utf-8') as f:
                file_lines = f.readlines()
            
            # Clean up source code lines for comparison
            source_lines = [line.rstrip() for line in source_code.split('\n') if line.strip()]
            if not source_lines:
                return 1, 1
            
            # Find the first line of source code in the file
            first_source_line = source_lines[0].strip()
            
            for i, file_line in enumerate(file_lines):
                if file_line.strip() == first_source_line:
                    # Found potential start, now verify the following lines match
                    start_line = i + 1  # Convert to 1-based indexing
                    match_count = 0
                    
                    for j, source_line in enumerate(source_lines):
                        if i + j < len(file_lines):
                            if file_lines[i + j].strip() == source_line.strip():
                                match_count += 1
                            else:
                                break
                        else:
                            break
                    
                    # If we matched all source lines, we found the location
                    if match_count == len(source_lines):
                        end_line = start_line + len(source_lines) - 1
                        return start_line, end_line
            
            # If exact match not found, return default
            return 1, len(source_lines)
            
        except Exception as e:
            # If file reading fails, return default
            return 1, len(source_code.split('\n'))
    
    def _parse_rust_function(self, line: str) -> tuple:
        """Parse Rust function definition"""
        import re
        
        # Extract function name
        fn_match = re.search(r'fn\s+(\w+)', line)
        function_name = fn_match.group(1) if fn_match else ""
        
        # Extract parameters
        parameters = []
        param_match = re.search(r'\((.*?)\)', line)
        if param_match:
            param_str = param_match.group(1).strip()
            if param_str and param_str != "&self" and param_str != "self":
                # Split parameters by comma
                param_parts = param_str.split(',')
                for param in param_parts:
                    param = param.strip()
                    if param and param != "&self" and param != "self":
                        # Parse "name: type" format
                        if ':' in param:
                            name_part, type_part = param.split(':', 1)
                            param_name = name_part.strip()
                            param_type = type_part.strip()
                            parameters.append({
                                "name": param_name,
                                "type": param_type
                            })
        
        # Format function signature
        if parameters:
            param_types = [p["type"] for p in parameters]
            function_signature = f"{function_name}({','.join(param_types)})"
        else:
            function_signature = f"{function_name}()"
        
        return function_signature, parameters
    
    def _parse_solidity_function(self, line: str) -> tuple:
        """Parse Solidity function definition"""
        import re
        
        # Extract function name
        fn_match = re.search(r'function\s+(\w+)', line)
        function_name = fn_match.group(1) if fn_match else ""
        
        # Extract parameters
        parameters = []
        param_match = re.search(r'\((.*?)\)', line)
        if param_match:
            param_str = param_match.group(1).strip()
            if param_str:
                param_parts = param_str.split(',')
                for param in param_parts:
                    param = param.strip()
                    if param:
                        # Parse "type name" format
                        parts = param.split()
                        if len(parts) >= 2:
                            param_type = parts[0]
                            param_name = parts[1]
                            parameters.append({
                                "name": param_name,
                                "type": param_type
                            })
        
        # Format function signature
        if parameters:
            param_types = [p["type"] for p in parameters]
            function_signature = f"{function_name}({','.join(param_types)})"
        else:
            function_signature = f"{function_name}()"
        
        return function_signature, parameters


class StructAnalyzer(BaseAnalyzer):
    """Struct analyzer"""
    
    def analyze(self) -> AnalysisResult:
        """Execute struct analysis"""
        import time
        start_time = time.time()
        
        if not self._validate_project_path():
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.STRUCT_ANALYZER,
                config=self.config,
                error_message=f"Invalid project path: {self.config.project_path}"
            )
        
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            import importlib.util
            spec = importlib.util.spec_from_file_location("struct_analyzer", Path(__file__).parent / "struct-anayzer.py")
            struct_analyzer_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(struct_analyzer_module)
            SolanaStructExtractor = struct_analyzer_module.SolanaStructExtractor
            
            extractor = SolanaStructExtractor(self.config.project_path)
            extractor.extract_from_project()
            
            output_path = self._generate_output_path("structs")
            if output_path:
                rust_output_path = output_path.replace('.json', '.rs')
                extractor.export_to_rust_file(rust_output_path)
                output_path = rust_output_path
            else:
                output_path = None
            
            data = {
                "project_path": self.config.project_path,
                "structs_count": len(extractor.structs),
                "constants_count": len(extractor.constants),
                "program_ids_count": len(extractor.program_ids),
                "oracle_infos_count": len(extractor.oracle_infos),
                "liquidity_pools_count": len(extractor.liquidity_pools),
                "lending_pools_count": len(extractor.lending_pools),
                "vaults_count": len(extractor.vaults),
                "governance_infos_count": len(extractor.governance_infos),
                "summary": f"Extracted {len(extractor.structs)} structs, {len(extractor.constants)} constants, {len(extractor.program_ids)} program IDs"
            }
            
            return AnalysisResult(
                success=True,
                analyzer_type=AnalyzerType.STRUCT_ANALYZER,
                config=self.config,
                data=data,
                output_path=rust_output_path,
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.STRUCT_ANALYZER,
                config=self.config,
                error_message=f"Error during struct analysis: {e}",
                execution_time=time.time() - start_time
            )


class CallGraphAnalyzer(BaseAnalyzer):
    """Call graph analyzer"""
    
    def analyze(self) -> AnalysisResult:
        """Execute call graph analysis"""
        import time
        start_time = time.time()
        
        if not self._validate_project_path():
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.CALL_GRAPH,
                config=self.config,
                error_message=f"Invalid project path: {self.config.project_path}"
            )
        
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_output_path = temp_file.name
            
            try:
                success = self._run_rust_analyzer_call_hierarchy(temp_output_path)
                if not success:
                    return AnalysisResult(
                        success=False,
                        analyzer_type=AnalyzerType.CALL_GRAPH,
                        config=self.config,
                        error_message="rust-analyzer call hierarchy analysis failed"
                    )
                
                json_output_path = self._run_json_analyzer(temp_output_path)
                if not json_output_path:
                    return AnalysisResult(
                        success=False,
                        analyzer_type=AnalyzerType.CALL_GRAPH,
                        config=self.config,
                        error_message="JSON analysis failed"
                    )
                
                data = None
                if os.path.exists(json_output_path):
                    with open(json_output_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                
                final_output_path = self._generate_output_path("call_graph")
                if final_output_path and final_output_path != json_output_path:
                    os.makedirs(os.path.dirname(final_output_path), exist_ok=True)
                    import shutil
                    shutil.move(json_output_path, final_output_path)
                    json_output_path = final_output_path
                
                return AnalysisResult(
                    success=True,
                    analyzer_type=AnalyzerType.CALL_GRAPH,
                    config=self.config,
                    data=data,
                    output_path=json_output_path,
                    execution_time=time.time() - start_time
                )
                
            finally:
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.CALL_GRAPH,
                config=self.config,
                error_message=f"Error during call graph analysis: {e}",
                execution_time=time.time() - start_time
            )
    
    def _run_rust_analyzer_call_hierarchy(self, output_file: str) -> bool:
        """Run rust-analyzer call hierarchy analysis"""
        try:
            print("Building rust-analyzer...")
            build_cmd = ["cargo", "build", "--release"]
            build_result = subprocess.run(
                build_cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                print(f"Failed to build rust-analyzer: {build_result.stderr}")
                return False
            
            print(f"Analyzing project: {self.config.project_path}")
            binary_path = self.project_root / "target" / "release" / "rust-analyzer"
            
            analysis_cmd = [
                str(binary_path),
                "function-analyzer",
                str(Path(self.config.project_path).resolve()),
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
            
            print("Call hierarchy analysis completed")
            return True
            
        except Exception as e:
            print(f"Error running rust-analyzer: {e}")
            return False
    
    def _run_json_analyzer(self, input_file: str) -> Optional[str]:
        """Run JSON analyzer"""
        try:
            analyzer_script = Path(__file__).parent / "funcation-anayzer.py"
            
            print(f"Generating JSON analysis results: {input_file}")
            
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
            
            output_lines = json_result.stdout.strip().split('\n')
            for line in output_lines:
                if "Results saved to:" in line:
                    return line.split("Results saved to:")[1].strip()
            
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


class AnalyzerFactory:
    """Analyzer factory"""
    
    @staticmethod
    def create_analyzer(config: AnalysisConfig) -> BaseAnalyzer:
        """Create analyzer based on config"""
        if config.analyzer_type == AnalyzerType.SOURCE_FINDER:
            return SourceFinderAnalyzer(config)
        elif config.analyzer_type == AnalyzerType.STRUCT_ANALYZER:
            return StructAnalyzer(config)
        elif config.analyzer_type == AnalyzerType.CALL_GRAPH:
            return CallGraphAnalyzer(config)
        else:
            raise ValueError(f"Unsupported analyzer type: {config.analyzer_type}")


class RustProjectAnalyzer:
    """Rust project analyzer main class"""
    
    def __init__(self, output_handler: Optional[OutputHandler] = None):
        self.output_handler = output_handler or FileOutputHandler()
    
    def analyze(self, config: AnalysisConfig) -> AnalysisResult:
        """Execute analysis"""
        try:
            analyzer = AnalyzerFactory.create_analyzer(config)
            result = analyzer.analyze()
            
            # Handle output for all analyzer types
            if result.success and self.output_handler:
                self.output_handler.handle_output(result)
            
            return result
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer_type=config.analyzer_type,
                config=config,
                error_message=f"Error during analysis: {e}"
            )
    
    def set_output_handler(self, handler: OutputHandler):
        """Set output handler"""
        self.output_handler = handler


# Convenience functions for programmatic use
def analyze_source(project_path: str, symbol_name: str,
                   output_path: Optional[str] = None, **kwargs) -> AnalysisResult:
    """Source analysis convenience function"""
    config = AnalysisConfig(
        project_path=project_path,
        analyzer_type=AnalyzerType.SOURCE_FINDER,
        symbol_name=symbol_name,
        output_path=output_path,
        **kwargs
    )
    
    analyzer = RustProjectAnalyzer()
    return analyzer.analyze(config)


def analyze_structs(project_path: str, output_path: Optional[str] = None, **kwargs) -> AnalysisResult:
    """Struct analysis convenience function"""
    config = AnalysisConfig(
        project_path=project_path,
        analyzer_type=AnalyzerType.STRUCT_ANALYZER,
        output_path=output_path,
        **kwargs
    )
    
    analyzer = RustProjectAnalyzer()
    return analyzer.analyze(config)


def analyze_call_graph(project_path: str, output_path: Optional[str] = None, **kwargs) -> AnalysisResult:
    """Call graph analysis convenience function"""
    config = AnalysisConfig(
        project_path=project_path,
        analyzer_type=AnalyzerType.CALL_GRAPH,
        output_path=output_path,
        **kwargs
    )
    
    analyzer = RustProjectAnalyzer()
    return analyzer.analyze(config)