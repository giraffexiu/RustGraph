# Rust Call Graph Analyzer

[English](#english) | [中文](#中文)

---

## English

### Overview

Rust Call Graph Analyzer is a powerful static analysis tool built on top of rust-analyzer that extracts and analyzes function call relationships in Rust projects. It's specifically optimized for Solana/Anchor blockchain projects but works with any Rust codebase.

### Key Features

- **🔍 Comprehensive Function Discovery**: Automatically discovers all functions across your entire Rust project
- **📊 Call Relationship Analysis**: Analyzes caller-callee relationships with precise source location information
- **🎯 Smart Filtering**: Intelligently filters out external dependencies to focus on your project code
- **📝 Detailed Output**: Generates human-readable text reports with file paths and line numbers
- **⚡ Fast Analysis**: Built on rust-analyzer's powerful semantic analysis engine
- **🔗 Anchor Framework Support**: Optimized for Solana/Anchor project analysis

### How It Works

The tool leverages rust-analyzer's semantic analysis capabilities to:

1. **Load Project**: Discovers and loads your Rust project workspace
2. **Extract Functions**: Traverses all modules and impl blocks to find function definitions
3. **Analyze Calls**: Uses rust-analyzer's call hierarchy API to identify function calls
4. **Filter Results**: Removes external library calls to focus on project-internal relationships
5. **Generate Report**: Outputs detailed call relationship information

### Installation

#### Prerequisites

- Rust 1.88+ 
- Cargo

#### Build from Source

```bash
# Clone the repository
git clone <repository-url>
cd rust-call-graph-analyzer

# Build the tool
cargo build --release
```

### Usage

#### Basic Usage

```bash
# Analyze current directory
./target/release/rust-analyzer function-analyzer .

# Analyze specific project path
./target/release/rust-analyzer function-analyzer /path/to/your/rust/project

# Save output to file
./target/release/rust-analyzer function-analyzer /path/to/project --output call_graph.txt
```

#### Command Line Options

```bash
rust-analyzer function-analyzer [OPTIONS] <PROJECT_PATH>

Arguments:
  <PROJECT_PATH>  Path to the Rust project to analyze

Options:
  -o, --output <FILE>              Output file path (default: stdout)
  --disable-build-scripts         Disable build script execution
  --disable-proc-macros           Disable procedural macro expansion
  --proc-macro-srv <PATH>         Custom proc-macro server path
  -h, --help                      Print help information
```

### Output Format

The tool generates a detailed text report showing function call relationships:

```
# Function Call Hierarchy Analysis
# Format: caller_function -> callee_function (call_site)

src/lib.rs:15:initialize -> src/config.rs:23:load_config (call at 18:5)
src/lib.rs:15:initialize -> src/utils.rs:45:setup_logging (call at 19:5)
src/processor.rs:67:process_instruction -> src/state.rs:34:update_state (call at 72:9)
```

Each line shows:
- **Caller**: `file_path:line:function_name`
- **Callee**: `file_path:line:function_name` 
- **Call Site**: `(call at line:column)`

### Use Cases

- **Code Understanding**: Quickly understand function call flows in large codebases
- **Dependency Analysis**: Identify which functions depend on others
- **Refactoring Support**: Safely refactor by understanding call relationships
- **Security Auditing**: Trace execution paths in Solana/Anchor programs
- **Documentation**: Generate call graphs for documentation purposes

### Architecture

The tool consists of several key components:

- **Function Extractor**: Discovers all functions using HIR (High-level Intermediate Representation)
- **Call Analyzer**: Uses rust-analyzer's call hierarchy API for precise call detection
- **Path Filter**: Intelligently filters external dependencies
- **Report Generator**: Formats output with relative paths and readable format

### Limitations

- Only analyzes static function calls (no dynamic dispatch analysis)
- Requires valid Rust project with `Cargo.toml`
- Large projects may take time to analyze
- Macro-generated code analysis depends on proc-macro expansion

---

## 中文

### 概述

Rust Call Graph Analyzer 是一个基于 rust-analyzer 构建的强大静态分析工具，用于提取和分析 Rust 项目中的函数调用关系。它专门针对 Solana/Anchor 区块链项目进行了优化，但适用于任何 Rust 代码库。

### 主要特性

- **🔍 全面的函数发现**: 自动发现整个 Rust 项目中的所有函数
- **📊 调用关系分析**: 分析调用者-被调用者关系，提供精确的源码位置信息
- **🎯 智能过滤**: 智能过滤外部依赖，专注于项目代码
- **📝 详细输出**: 生成包含文件路径和行号的可读文本报告
- **⚡ 快速分析**: 基于 rust-analyzer 强大的语义分析引擎构建
- **🔗 Anchor 框架支持**: 针对 Solana/Anchor 项目分析进行优化

### 工作原理

该工具利用 rust-analyzer 的语义分析能力：

1. **加载项目**: 发现并加载 Rust 项目工作空间
2. **提取函数**: 遍历所有模块和 impl 块以查找函数定义
3. **分析调用**: 使用 rust-analyzer 的调用层次 API 识别函数调用
4. **过滤结果**: 移除外部库调用，专注于项目内部关系
5. **生成报告**: 输出详细的调用关系信息

### 安装

#### 前置要求

- Rust 1.88+
- Cargo

#### 从源码构建

```bash
# 克隆仓库
git clone <repository-url>
cd rust-call-graph-analyzer

# 构建工具
cargo build --release
```

### 使用方法

#### 基本用法

```bash
# 分析当前目录
./target/release/rust-analyzer function-analyzer .

# 分析特定项目路径
./target/release/rust-analyzer function-analyzer /path/to/your/rust/project

# 保存输出到文件
./target/release/rust-analyzer function-analyzer /path/to/project --output call_graph.txt
```

#### 命令行选项

```bash
rust-analyzer function-analyzer [OPTIONS] <PROJECT_PATH>

参数:
  <PROJECT_PATH>  要分析的 Rust 项目路径

选项:
  -o, --output <FILE>              输出文件路径（默认：stdout）
  --disable-build-scripts         禁用构建脚本执行
  --disable-proc-macros           禁用过程宏展开
  --proc-macro-srv <PATH>         自定义过程宏服务器路径
  -h, --help                      打印帮助信息
```

### 输出格式

工具生成显示函数调用关系的详细文本报告：

```
# Function Call Hierarchy Analysis
# Format: caller_function -> callee_function (call_site)

src/lib.rs:15:initialize -> src/config.rs:23:load_config (call at 18:5)
src/lib.rs:15:initialize -> src/utils.rs:45:setup_logging (call at 19:5)
src/processor.rs:67:process_instruction -> src/state.rs:34:update_state (call at 72:9)
```

每行显示：
- **调用者**: `文件路径:行号:函数名`
- **被调用者**: `文件路径:行号:函数名`
- **调用点**: `(call at 行号:列号)`

### 使用场景

- **代码理解**: 快速理解大型代码库中的函数调用流程
- **依赖分析**: 识别哪些函数依赖于其他函数
- **重构支持**: 通过理解调用关系安全地进行重构
- **安全审计**: 追踪 Solana/Anchor 程序中的执行路径
- **文档生成**: 为文档目的生成调用图

### 架构

工具由几个关键组件组成：

- **函数提取器**: 使用 HIR（高级中间表示）发现所有函数
- **调用分析器**: 使用 rust-analyzer 的调用层次 API 进行精确的调用检测
- **路径过滤器**: 智能过滤外部依赖
- **报告生成器**: 使用相对路径和可读格式格式化输出

### 限制

- 仅分析静态函数调用（不分析动态分发）
- 需要包含 `Cargo.toml` 的有效 Rust 项目
- 大型项目可能需要时间分析
- 宏生成的代码分析依赖于过程宏展开

### 贡献

欢迎贡献！请查看我们的贡献指南了解更多信息。

### 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。