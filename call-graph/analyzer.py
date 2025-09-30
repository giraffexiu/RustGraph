#!/usr/bin/env python3
"""
Rust Project Analyzer Core Module

统一的Rust项目分析核心模块，整合符号查找、结构体分析和调用图分析功能。
提供命令行和程序化调用两种接口模式。
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
    """分析器类型枚举"""
    SYMBOL_FINDER = "symbol_finder"
    STRUCT_ANALYZER = "struct_analyzer"
    CALL_GRAPH = "call_graph"


class OutputFormat(Enum):
    """输出格式枚举"""
    JSON = "json"
    TEXT = "text"
    DICT = "dict"  # 用于程序化调用


@dataclass
class AnalysisConfig:
    """分析配置"""
    project_path: str
    analyzer_type: AnalyzerType
    output_format: OutputFormat = OutputFormat.JSON
    output_path: Optional[str] = None
    
    # 符号查找特定配置
    symbol_type: Optional[str] = None  # "function", "struct"
    symbol_name: Optional[str] = None
    
    # 通用配置
    disable_build_scripts: bool = False
    disable_proc_macros: bool = False
    proc_macro_srv: Optional[str] = None
    
    # 输出配置
    auto_generate_output_path: bool = True
    output_base_dir: str = field(default_factory=lambda: str(Path(__file__).parent / "output"))


@dataclass
class AnalysisResult:
    """分析结果"""
    success: bool
    analyzer_type: AnalyzerType
    config: AnalysisConfig
    data: Optional[Dict[str, Any]] = None
    output_path: Optional[str] = None
    error_message: Optional[str] = None
    execution_time: Optional[float] = None


class OutputHandler(ABC):
    """输出处理器抽象基类"""
    
    @abstractmethod
    def handle_output(self, result: AnalysisResult) -> bool:
        """处理输出结果"""
        pass


class FileOutputHandler(OutputHandler):
    """文件输出处理器"""
    
    def handle_output(self, result: AnalysisResult) -> bool:
        """将结果输出到文件"""
        if not result.success or not result.data:
            return False
        
        try:
            output_path = result.output_path
            if not output_path:
                return False
            
            # 确保输出目录存在
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if result.config.output_format == OutputFormat.JSON:
                    json.dump(result.data, f, indent=2, ensure_ascii=False)
                else:
                    f.write(str(result.data))
            
            print(f"分析结果已保存到: {output_path}")
            return True
            
        except Exception as e:
            print(f"保存结果失败: {e}")
            return False


class CallbackOutputHandler(OutputHandler):
    """回调输出处理器，用于程序化调用"""
    
    def __init__(self, callback: Callable[[AnalysisResult], bool]):
        self.callback = callback
    
    def handle_output(self, result: AnalysisResult) -> bool:
        """通过回调函数处理结果"""
        return self.callback(result)


class BaseAnalyzer(ABC):
    """分析器基类"""
    
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.project_root = Path(__file__).parent.parent
    
    @abstractmethod
    def analyze(self) -> AnalysisResult:
        """执行分析"""
        pass
    
    def _validate_project_path(self) -> bool:
        """验证项目路径"""
        project_path = Path(self.config.project_path)
        
        if not project_path.exists():
            return False
        
        # 检查是否是Rust项目
        cargo_toml = project_path / "Cargo.toml"
        if not cargo_toml.exists():
            return False
        
        return True
    
    def _generate_output_path(self, suffix: str) -> str:
        """生成输出文件路径"""
        if self.config.output_path:
            return self.config.output_path
        
        if not self.config.auto_generate_output_path:
            return None
        
        # 基于项目名称生成输出路径
        project_name = Path(self.config.project_path).name
        output_dir = Path(self.config.output_base_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.config.output_format == OutputFormat.JSON:
            filename = f"{project_name}_{suffix}.json"
        else:
            filename = f"{project_name}_{suffix}.txt"
        
        return str(output_dir / filename)


class SymbolFinderAnalyzer(BaseAnalyzer):
    """符号查找分析器"""
    
    def analyze(self) -> AnalysisResult:
        """执行符号查找分析"""
        import time
        start_time = time.time()
        
        if not self._validate_project_path():
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.SYMBOL_FINDER,
                config=self.config,
                error_message=f"无效的项目路径: {self.config.project_path}"
            )
        
        if not self.config.symbol_type or not self.config.symbol_name:
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.SYMBOL_FINDER,
                config=self.config,
                error_message="符号查找需要指定symbol_type和symbol_name"
            )
        
        try:
            # 构建rust-analyzer命令
            binary_path = self.project_root / "target" / "release" / "rust-analyzer"
            
            # 确保rust-analyzer已构建
            if not binary_path.exists():
                self._build_rust_analyzer()
            
            cmd = [
                str(binary_path),
                "symbol-finder",
                self.config.symbol_type,
                self.config.symbol_name,
                "--project-path", self.config.project_path,
                "--output-format", "json"
            ]
            
            # 符号查找不输出到文件，直接从stdout获取结果
            
            if self.config.disable_build_scripts:
                cmd.append("--disable-build-scripts")
            
            if self.config.disable_proc_macros:
                cmd.append("--disable-proc-macros")
            
            if self.config.proc_macro_srv:
                cmd.extend(["--proc-macro-srv", self.config.proc_macro_srv])
            
            # 执行命令
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                return AnalysisResult(
                    success=False,
                    analyzer_type=AnalyzerType.SYMBOL_FINDER,
                    config=self.config,
                    error_message=f"符号查找失败: {result.stderr}",
                    execution_time=time.time() - start_time
                )
            
            # 解析输出结果
            data = None
            if result.stdout:
                try:
                    data = json.loads(result.stdout)
                except json.JSONDecodeError:
                    data = {"output": result.stdout}
            else:
                # 如果没有stdout输出，但命令成功执行，创建一个包含stderr信息的结果
                data = {"message": "符号查找完成", "stderr": result.stderr}
            
            return AnalysisResult(
                success=True,
                analyzer_type=AnalyzerType.SYMBOL_FINDER,
                config=self.config,
                data=data,
                output_path=None,  # 符号查找不输出文件
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.SYMBOL_FINDER,
                config=self.config,
                error_message=f"执行符号查找时发生错误: {e}",
                execution_time=time.time() - start_time
            )
    
    def _build_rust_analyzer(self):
        """构建rust-analyzer"""
        print("正在构建rust-analyzer...")
        build_cmd = ["cargo", "build", "--release"]
        build_result = subprocess.run(
            build_cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        if build_result.returncode != 0:
            raise Exception(f"构建rust-analyzer失败: {build_result.stderr}")


class StructAnalyzer(BaseAnalyzer):
    """结构体分析器"""
    
    def analyze(self) -> AnalysisResult:
        """执行结构体分析"""
        import time
        start_time = time.time()
        
        if not self._validate_project_path():
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.STRUCT_ANALYZER,
                config=self.config,
                error_message=f"无效的项目路径: {self.config.project_path}"
            )
        
        try:
            # 导入并使用struct-analyzer
            sys.path.insert(0, str(Path(__file__).parent))
            import importlib.util
            spec = importlib.util.spec_from_file_location("struct_analyzer", Path(__file__).parent / "struct-analyzer.py")
            struct_analyzer_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(struct_analyzer_module)
            SolanaStructExtractor = struct_analyzer_module.SolanaStructExtractor
            
            # 创建提取器并执行分析
            extractor = SolanaStructExtractor(self.config.project_path)
            extractor.extract_from_project()
            
            # 直接调用struct-analyzer的输出方法，不保存JSON文件
            output_path = self._generate_output_path("structs")
            if output_path:
                # 使用struct-analyzer自带的export_to_rust_file方法
                rust_output_path = output_path.replace('.json', '.rs')
                extractor.export_to_rust_file(rust_output_path)
                output_path = rust_output_path
            else:
                output_path = None
            
            # 构建结果数据用于返回
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
                "summary": f"提取了 {len(extractor.structs)} 个结构体, {len(extractor.constants)} 个常量, {len(extractor.program_ids)} 个程序ID"
            }
            
            return AnalysisResult(
                success=True,
                analyzer_type=AnalyzerType.STRUCT_ANALYZER,
                config=self.config,
                data=data,
                output_path=rust_output_path,  # 返回.rs文件路径
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.STRUCT_ANALYZER,
                config=self.config,
                error_message=f"执行结构体分析时发生错误: {e}",
                execution_time=time.time() - start_time
            )


class CallGraphAnalyzer(BaseAnalyzer):
    """调用图分析器"""
    
    def analyze(self) -> AnalysisResult:
        """执行调用图分析"""
        import time
        start_time = time.time()
        
        if not self._validate_project_path():
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.CALL_GRAPH,
                config=self.config,
                error_message=f"无效的项目路径: {self.config.project_path}"
            )
        
        try:
            # 使用analyze_project.py的逻辑
            sys.path.insert(0, str(Path(__file__).parent))
            
            # 运行rust-analyzer调用层次分析
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_output_path = temp_file.name
            
            try:
                success = self._run_rust_analyzer_call_hierarchy(temp_output_path)
                if not success:
                    return AnalysisResult(
                        success=False,
                        analyzer_type=AnalyzerType.CALL_GRAPH,
                        config=self.config,
                        error_message="rust-analyzer调用层次分析失败"
                    )
                
                # 运行JSON分析
                json_output_path = self._run_json_analyzer(temp_output_path)
                if not json_output_path:
                    return AnalysisResult(
                        success=False,
                        analyzer_type=AnalyzerType.CALL_GRAPH,
                        config=self.config,
                        error_message="JSON分析失败"
                    )
                
                # 读取结果数据
                data = None
                if os.path.exists(json_output_path):
                    with open(json_output_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                
                # 如果需要，移动到指定输出路径
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
                # 清理临时文件
                if os.path.exists(temp_output_path):
                    os.unlink(temp_output_path)
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer_type=AnalyzerType.CALL_GRAPH,
                config=self.config,
                error_message=f"执行调用图分析时发生错误: {e}",
                execution_time=time.time() - start_time
            )
    
    def _run_rust_analyzer_call_hierarchy(self, output_file: str) -> bool:
        """运行rust-analyzer调用层次分析"""
        try:
            # 构建rust-analyzer
            print("正在构建rust-analyzer...")
            build_cmd = ["cargo", "build", "--release"]
            build_result = subprocess.run(
                build_cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if build_result.returncode != 0:
                print(f"构建rust-analyzer失败: {build_result.stderr}")
                return False
            
            # 运行调用层次分析
            print(f"正在分析项目: {self.config.project_path}")
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
                print(f"调用层次分析失败: {analysis_result.stderr}")
                return False
            
            print("调用层次分析完成")
            return True
            
        except Exception as e:
            print(f"运行rust-analyzer时发生错误: {e}")
            return False
    
    def _run_json_analyzer(self, input_file: str) -> Optional[str]:
        """运行JSON分析器"""
        try:
            analyzer_script = Path(__file__).parent / "json_processor.py"
            
            print(f"正在生成JSON分析结果: {input_file}")
            
            json_cmd = [sys.executable, str(analyzer_script), input_file]
            json_result = subprocess.run(
                json_cmd,
                capture_output=True,
                text=True,
                cwd=Path(__file__).parent
            )
            
            if json_result.returncode != 0:
                print(f"JSON分析失败: {json_result.stderr}")
                return None
            
            # 从输出中提取结果文件路径
            output_lines = json_result.stdout.strip().split('\n')
            for line in output_lines:
                if "Results saved to:" in line:
                    return line.split("Results saved to:")[1].strip()
            
            # 备用方案：构建预期路径
            input_basename = os.path.basename(input_file)
            input_name, _ = os.path.splitext(input_basename)
            output_dir = Path(__file__).parent / "output"
            expected_json_path = output_dir / f"{input_name}_call_graph.json"
            
            if expected_json_path.exists():
                return str(expected_json_path)
            
            return None
            
        except Exception as e:
            print(f"运行JSON分析器时发生错误: {e}")
            return None


class AnalyzerFactory:
    """分析器工厂"""
    
    @staticmethod
    def create_analyzer(config: AnalysisConfig) -> BaseAnalyzer:
        """根据配置创建相应的分析器"""
        if config.analyzer_type == AnalyzerType.SYMBOL_FINDER:
            return SymbolFinderAnalyzer(config)
        elif config.analyzer_type == AnalyzerType.STRUCT_ANALYZER:
            return StructAnalyzer(config)
        elif config.analyzer_type == AnalyzerType.CALL_GRAPH:
            return CallGraphAnalyzer(config)
        else:
            raise ValueError(f"不支持的分析器类型: {config.analyzer_type}")


class RustProjectAnalyzer:
    """Rust项目分析器主类"""
    
    def __init__(self, output_handler: Optional[OutputHandler] = None):
        self.output_handler = output_handler or FileOutputHandler()
    
    def analyze(self, config: AnalysisConfig) -> AnalysisResult:
        """执行分析"""
        try:
            # 创建分析器
            analyzer = AnalyzerFactory.create_analyzer(config)
            
            # 执行分析
            result = analyzer.analyze()
            
            # 只有在非struct-analyzer的情况下才处理输出
            # struct-analyzer已经通过export_to_rust_file()输出了.rs文件
            if result.success and self.output_handler and config.analyzer_type != AnalyzerType.STRUCT_ANALYZER:
                self.output_handler.handle_output(result)
            
            return result
            
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer_type=config.analyzer_type,
                config=config,
                error_message=f"分析过程中发生错误: {e}"
            )
    
    def set_output_handler(self, handler: OutputHandler):
        """设置输出处理器"""
        self.output_handler = handler


# 便捷函数，用于程序化调用
def analyze_symbols(project_path: str, symbol_type: str, symbol_name: str, 
                   output_path: Optional[str] = None, **kwargs) -> AnalysisResult:
    """符号分析便捷函数"""
    config = AnalysisConfig(
        project_path=project_path,
        analyzer_type=AnalyzerType.SYMBOL_FINDER,
        symbol_type=symbol_type,
        symbol_name=symbol_name,
        output_path=output_path,
        **kwargs
    )
    
    analyzer = RustProjectAnalyzer()
    return analyzer.analyze(config)


def analyze_structs(project_path: str, output_path: Optional[str] = None, **kwargs) -> AnalysisResult:
    """结构体分析便捷函数"""
    config = AnalysisConfig(
        project_path=project_path,
        analyzer_type=AnalyzerType.STRUCT_ANALYZER,
        output_path=output_path,
        **kwargs
    )
    
    analyzer = RustProjectAnalyzer()
    return analyzer.analyze(config)


def analyze_call_graph(project_path: str, output_path: Optional[str] = None, **kwargs) -> AnalysisResult:
    """调用图分析便捷函数"""
    config = AnalysisConfig(
        project_path=project_path,
        analyzer_type=AnalyzerType.CALL_GRAPH,
        output_path=output_path,
        **kwargs
    )
    
    analyzer = RustProjectAnalyzer()
    return analyzer.analyze(config)