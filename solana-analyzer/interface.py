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
            
            # Return source code directly without any wrapper
            source_code = result.stdout.strip() if result.stdout else ""
            data = {"source_code": source_code}
            
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