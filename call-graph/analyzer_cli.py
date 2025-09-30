#!/usr/bin/env python3
"""
Rust Project Analyzer CLI

统一的命令行接口，整合符号查找、结构体分析和调用图分析功能。
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Optional

# 添加当前目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from analyzer_core import (
    RustProjectAnalyzer, AnalysisConfig, AnalyzerType, OutputFormat,
    FileOutputHandler, CallbackOutputHandler
)


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="Rust项目分析工具 - 统一的符号查找、结构体分析和调用图分析接口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 符号查找
  python analyzer_cli.py symbol-finder function my_function /path/to/project
  
  # 结构体分析
  python analyzer_cli.py struct-analyzer /path/to/project
  
  # 调用图分析
  python analyzer_cli.py call-graph /path/to/project
        """
    )
    
    # 全局参数
    parser.add_argument(
        "--disable-build-scripts",
        action="store_true",
        help="禁用构建脚本"
    )
    
    parser.add_argument(
        "--disable-proc-macros",
        action="store_true",
        help="禁用过程宏"
    )
    
    parser.add_argument(
        "--proc-macro-srv",
        type=str,
        help="过程宏服务器路径"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="详细输出"
    )
    
    # 子命令
    subparsers = parser.add_subparsers(
        dest="analyzer_type",
        help="分析器类型",
        required=True
    )
    
    # 符号查找子命令
    symbol_parser = subparsers.add_parser(
        "symbol-finder",
        help="符号查找分析器"
    )
    symbol_parser.add_argument(
        "symbol_type",
        choices=["function", "struct", "fn"],
        help="符号类型"
    )
    symbol_parser.add_argument(
        "symbol_name",
        help="符号名称"
    )
    symbol_parser.add_argument(
        "project_path",
        help="Rust项目路径"
    )
    
    # 结构体分析子命令
    struct_parser = subparsers.add_parser(
        "struct-analyzer",
        help="结构体分析器"
    )
    struct_parser.add_argument(
        "project_path",
        help="Rust项目路径"
    )
    
    # 调用图分析子命令
    call_graph_parser = subparsers.add_parser(
        "call-graph",
        help="调用图分析器"
    )
    call_graph_parser.add_argument(
        "project_path",
        help="Rust项目路径"
    )
    
    return parser


def validate_args(args) -> bool:
    """验证命令行参数"""
    # 验证项目路径
    project_path = Path(args.project_path)
    if not project_path.exists():
        print(f"错误: 项目路径不存在: {args.project_path}")
        return False
    
    # 检查是否是Rust项目
    cargo_toml = project_path / "Cargo.toml"
    if not cargo_toml.exists():
        print(f"错误: 指定路径不是Rust项目（未找到Cargo.toml）: {args.project_path}")
        return False
    
    return True


def create_config_from_args(args) -> AnalysisConfig:
    """从命令行参数创建分析配置"""
    # 确定分析器类型
    analyzer_type_map = {
        "symbol-finder": AnalyzerType.SYMBOL_FINDER,
        "struct-analyzer": AnalyzerType.STRUCT_ANALYZER,
        "call-graph": AnalyzerType.CALL_GRAPH
    }
    
    analyzer_type = analyzer_type_map[args.analyzer_type]
    
    # 创建配置
    config = AnalysisConfig(
        project_path=args.project_path,
        analyzer_type=analyzer_type,
        output_format=OutputFormat.JSON,  # 默认JSON格式
        output_path=None,  # 符号查找不输出文件
        output_base_dir=str(Path(__file__).parent / "output"),  # 其他分析器的默认输出目录
        disable_build_scripts=args.disable_build_scripts,
        disable_proc_macros=args.disable_proc_macros,
        proc_macro_srv=args.proc_macro_srv
    )
    
    # 符号查找特定配置
    if analyzer_type == AnalyzerType.SYMBOL_FINDER:
        # 标准化符号类型
        symbol_type = args.symbol_type
        if symbol_type == "fn":
            symbol_type = "function"
        
        config.symbol_type = symbol_type
        config.symbol_name = args.symbol_name
    
    return config


def print_result_summary(result, verbose: bool = False):
    """打印结果摘要"""
    if result.success:
        print("✓ 分析完成")
        print(f"  分析器类型: {result.analyzer_type.value}")
        print(f"  项目路径: {result.config.project_path}")
        
        if result.execution_time:
            print(f"  执行时间: {result.execution_time:.2f}秒")
        
        # 对于符号查找，直接输出结果到控制台
        if result.analyzer_type == AnalyzerType.SYMBOL_FINDER and result.data:
            print("\n符号查找结果:")
            if isinstance(result.data, dict):
                import json
                print(json.dumps(result.data, indent=2, ensure_ascii=False))
            else:
                print(result.data)
        elif result.output_path:
            print(f"  输出文件: {result.output_path}")
        
        # 打印数据统计
        if result.data and verbose and result.analyzer_type != AnalyzerType.SYMBOL_FINDER:
            print("\n数据统计:")
            if result.analyzer_type == AnalyzerType.STRUCT_ANALYZER:
                print(f"  结构体: {result.data.get('structs_count', 0)}")
                print(f"  常量: {result.data.get('constants_count', 0)}")
                print(f"  程序ID: {result.data.get('program_ids_count', 0)}")
                print(f"  预言机信息: {result.data.get('oracle_infos_count', 0)}")
                print(f"  流动性池: {result.data.get('liquidity_pools_count', 0)}")
                print(f"  借贷池: {result.data.get('lending_pools_count', 0)}")
                print(f"  金库: {result.data.get('vaults_count', 0)}")
                print(f"  治理信息: {result.data.get('governance_infos_count', 0)}")
            elif result.analyzer_type == AnalyzerType.CALL_GRAPH:
                functions_count = len(result.data.get("functions", {}))
                print(f"  函数: {functions_count}")
    else:
        print("✗ 分析失败")
        print(f"  错误信息: {result.error_message}")
        if result.execution_time:
            print(f"  执行时间: {result.execution_time:.2f}秒")


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 验证参数
    if not validate_args(args):
        sys.exit(1)
    
    # 创建配置
    config = create_config_from_args(args)
    
    if args.verbose:
        print(f"开始分析项目: {config.project_path}")
        print(f"分析器类型: {config.analyzer_type.value}")
        print("=" * 60)
    
    # 创建分析器并执行分析
    analyzer = RustProjectAnalyzer()
    result = analyzer.analyze(config)
    
    # 打印结果
    if args.verbose:
        print("=" * 60)
    
    print_result_summary(result, args.verbose)
    
    # 设置退出码
    sys.exit(0 if result.success else 1)


if __name__ == "__main__":
    main()