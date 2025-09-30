"""
Rust Project Analyzer Library

统一的Rust项目分析库，提供符号查找、结构体分析和调用图分析功能。

主要功能:
- 符号查找: 在Rust项目中查找函数、结构体等符号
- 结构体分析: 提取Solana合约中的结构体、常量和程序ID
- 调用图分析: 分析项目中的函数调用关系

使用示例:
    # 作为库使用
    from rust_analyzer import analyze_symbols, analyze_structs, analyze_call_graph
    
    # 符号查找
    result = analyze_symbols("/path/to/project", "function", "my_function")
    
    # 结构体分析
    result = analyze_structs("/path/to/project")
    
    # 调用图分析
    result = analyze_call_graph("/path/to/project")
    
    # 使用回调处理结果
    def handle_result(result):
        print(f"分析完成: {result.success}")
        return result.data
    
    result = analyze_structs("/path/to/project", output_handler=handle_result)
"""

from .analyzer_core import (
    # 主要类
    RustProjectAnalyzer,
    AnalysisConfig,
    AnalysisResult,
    
    # 枚举类型
    AnalyzerType,
    OutputFormat,
    
    # 输出处理器
    OutputHandler,
    FileOutputHandler,
    CallbackOutputHandler,
    
    # 分析器基类和具体实现
    BaseAnalyzer,
    SymbolFinderAnalyzer,
    StructAnalyzer,
    CallGraphAnalyzer,
    AnalyzerFactory,
    
    # 便捷函数
    analyze_symbols,
    analyze_structs,
    analyze_call_graph,
)

# 版本信息
__version__ = "1.0.0"
__author__ = "Rust Project Analyzer Team"
__description__ = "统一的Rust项目分析库"

# 公共接口
__all__ = [
    # 主要类
    "RustProjectAnalyzer",
    "AnalysisConfig", 
    "AnalysisResult",
    
    # 枚举类型
    "AnalyzerType",
    "OutputFormat",
    
    # 输出处理器
    "OutputHandler",
    "FileOutputHandler", 
    "CallbackOutputHandler",
    
    # 分析器
    "BaseAnalyzer",
    "SymbolFinderAnalyzer",
    "StructAnalyzer",
    "CallGraphAnalyzer",
    "AnalyzerFactory",
    
    # 便捷函数
    "analyze_symbols",
    "analyze_structs", 
    "analyze_call_graph",
    
    # 元信息
    "__version__",
    "__author__",
    "__description__",
]

# 快速开始示例
def quick_start_example():
    """快速开始示例"""
    print("""
Rust Project Analyzer 快速开始:

1. 符号查找:
   from rust_analyzer import analyze_symbols
   result = analyze_symbols("/path/to/project", "function", "my_function")

2. 结构体分析:
   from rust_analyzer import analyze_structs  
   result = analyze_structs("/path/to/project")

3. 调用图分析:
   from rust_analyzer import analyze_call_graph
   result = analyze_call_graph("/path/to/project")

4. 使用配置:
   from rust_analyzer import RustProjectAnalyzer, AnalysisConfig, AnalyzerType
   
   config = AnalysisConfig(
       project_path="/path/to/project",
       analyzer_type=AnalyzerType.STRUCT_ANALYZER,
       output_path="/path/to/output.json"
   )
   
   analyzer = RustProjectAnalyzer()
   result = analyzer.analyze(config)

5. 自定义输出处理:
   from rust_analyzer import analyze_structs, CallbackOutputHandler
   
   def my_handler(result):
       print(f"找到 {len(result.data.get('structs', []))} 个结构体")
       return result.data
   
   result = analyze_structs("/path/to/project", output_handler=my_handler)
    """)

# 模块级别的便捷函数，提供更简单的接口
def analyze_project(project_path: str, analyzer_type: str = "struct", **kwargs):
    """
    通用项目分析函数
    
    Args:
        project_path: 项目路径
        analyzer_type: 分析器类型 ("symbol", "struct", "call-graph")
        **kwargs: 其他参数
    
    Returns:
        AnalysisResult: 分析结果
    """
    if analyzer_type == "symbol":
        symbol_type = kwargs.get("symbol_type", "function")
        symbol_name = kwargs.get("symbol_name", "")
        if not symbol_name:
            raise ValueError("符号查找需要指定symbol_name参数")
        return analyze_symbols(project_path, symbol_type, symbol_name, **kwargs)
    elif analyzer_type == "struct":
        return analyze_structs(project_path, **kwargs)
    elif analyzer_type == "call-graph":
        return analyze_call_graph(project_path, **kwargs)
    else:
        raise ValueError(f"不支持的分析器类型: {analyzer_type}")

# 添加到公共接口
__all__.extend(["quick_start_example", "analyze_project"])