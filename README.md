# RustGraph

[English](#english) | [中文](#中文)

---

## English

### Overview

RustGraph is a comprehensive static analysis toolkit for Rust projects, specifically optimized for Solana/Anchor blockchain development. It provides two powerful tools:

1. **Function Call Analyzer**: Extracts and analyzes function call relationships using rust-analyzer
2. **Solana Structure Extractor**: Extracts complete contract structures for AI vulnerability analysis

### Key Features

#### Function Call Analyzer
- **🔍 Comprehensive Function Discovery**: Automatically discovers all functions across your entire Rust project
- **📊 Call Relationship Analysis**: Analyzes caller-callee relationships with precise source location information
- **🎯 Smart Filtering**: Intelligently filters out external dependencies to focus on your project code
- **📝 Detailed Output**: Generates human-readable text reports with file paths and line numbers
- **⚡ Fast Analysis**: Built on rust-analyzer's powerful semantic analysis engine

#### Solana Structure Extractor
- **🏗️ Complete Structure Extraction**: Extracts complete struct definitions with all fields and constraints
- **🔐 Security-Focused**: Designed for AI vulnerability scanning and security auditing
- **🎯 DeFi Protocol Support**: Specialized extraction for DeFi-related structures (Oracle, Pool, Lending, Vault, Governance)
- **📋 Comprehensive Context**: Provides complete context to prevent cross-file misanalysis
- **🚀 Robust Parsing**: Uses advanced bracket matching algorithms for accurate extraction

### Tools

#### 1. Function Call Analyzer

Leverages rust-analyzer's semantic analysis capabilities to:

1. **Load Project**: Discovers and loads your Rust project workspace
2. **Extract Functions**: Traverses all modules and impl blocks to find function definitions
3. **Analyze Calls**: Uses rust-analyzer's call hierarchy API to identify function calls
4. **Filter Results**: Removes external library calls to focus on project-internal relationships
5. **Generate Report**: Outputs detailed call relationship information

#### 2. Solana Structure Extractor

Specialized tool for Solana/Anchor projects that:

1. **Discovers Structures**: Finds all struct definitions with `#[account]` and other attributes
2. **Extracts Complete Fields**: Uses robust bracket matching to extract all struct fields
3. **Captures Constraints**: Extracts account constraints and validation logic
4. **Identifies DeFi Components**: Recognizes Oracle, Pool, Lending, Vault, and Governance patterns
5. **Generates Context**: Outputs complete Rust code for AI analysis

### Installation

#### Prerequisites

- Rust 1.88+ 
- Cargo
- Python 3.7+ (for Solana Structure Extractor)

#### Build from Source

```bash
# Clone the repository
git clone <repository-url>
cd rustgraph

# Build the function analyzer
cargo build --release

# The Solana extractor is ready to use (Python script)
```

### Usage

#### Function Call Analyzer

```bash
# Analyze current directory
./target/release/rust-analyzer function-analyzer .

# Analyze specific project path
./target/release/rust-analyzer function-analyzer /path/to/your/rust/project

# Save output to file
./target/release/rust-analyzer function-analyzer /path/to/project --output call_graph.txt
```

#### Solana Structure Extractor

```bash
# Extract structures from Solana project
python3 call-graph/solana_extractor_v3.py /path/to/solana/project

# Specify output file
python3 call-graph/solana_extractor_v3.py /path/to/solana/project --output extracted_structures.rs

# Example with pump-science project
python3 call-graph/solana_extractor_v3.py ./2025-01-pump-science --output output/complete_structures.rs
```

### Output Formats

#### Function Call Analyzer Output

```
# Function Call Hierarchy Analysis
# Format: caller_function -> callee_function (call_site)

src/lib.rs:15:initialize -> src/config.rs:23:load_config (call at 18:5)
src/lib.rs:15:initialize -> src/utils.rs:45:setup_logging (call at 19:5)
src/processor.rs:67:process_instruction -> src/state.rs:34:update_state (call at 72:9)
```

#### Solana Structure Extractor Output

```rust
// Extracted Solana Contract Structures for AI Vulnerability Analysis
// Complete context to prevent cross-file misanalysis

use anchor_lang::prelude::*;

// ===== PROGRAM IDs =====
declare_id!("EtZR9gh25YUM6LkL2o2yYV1KzyuDdftHvYk3wsb2Ypkj");

// ===== CONSTANTS =====
pub const BASIS_POINTS_DIVISOR: u64 = 10_000;

// ===== COMPLETE STRUCT DEFINITIONS =====
#[derive(InitSpace, Debug)]
#[account]
pub struct Global {
    pub initialized: bool,
    pub global_authority: Pubkey,
    pub migration_authority: Pubkey,
    pub migrate_fee_amount: u64,
    // ... all fields extracted completely
}

// ===== GOVERNANCE =====
// Governance Type: admin
// Governance Type: migration
```

### Use Cases

#### Function Call Analyzer
- **Code Understanding**: Quickly understand function call flows in large codebases
- **Dependency Analysis**: Identify which functions depend on others
- **Refactoring Support**: Safely refactor by understanding call relationships
- **Security Auditing**: Trace execution paths in Solana/Anchor programs

#### Solana Structure Extractor
- **AI Vulnerability Scanning**: Provide complete context for AI-based security analysis
- **Security Auditing**: Extract all contract structures for manual review
- **Documentation**: Generate comprehensive structure documentation
- **Cross-file Analysis**: Prevent misanalysis due to incomplete struct definitions

### DeFi Protocol Support

The Solana Structure Extractor includes specialized support for:

- **🔮 Oracle Integration**: Switchboard, Pyth, Chainlink price feeds
- **💧 Liquidity Pools**: Constant product, stable swap, concentrated liquidity
- **💰 Lending Protocols**: Collateral ratios, liquidation thresholds, interest rates
- **🏦 Vault Strategies**: Yield farming, lending strategies, staking pools
- **🏛️ Governance**: Multi-sig, DAO, timelock mechanisms

### Architecture

#### Function Call Analyzer Components
- **Function Extractor**: Discovers all functions using HIR (High-level Intermediate Representation)
- **Call Analyzer**: Uses rust-analyzer's call hierarchy API for precise call detection
- **Path Filter**: Intelligently filters external dependencies
- **Report Generator**: Formats output with relative paths and readable format

#### Solana Structure Extractor Components
- **Structure Parser**: Robust bracket matching algorithm for complete extraction
- **Constraint Analyzer**: Extracts account constraints and validation logic
- **DeFi Pattern Matcher**: Recognizes common DeFi protocol patterns
- **Context Generator**: Outputs complete Rust code for analysis

### Limitations

#### Function Call Analyzer
- Only analyzes static function calls (no dynamic dispatch analysis)
- Requires valid Rust project with `Cargo.toml`
- Large projects may take time to analyze

#### Solana Structure Extractor
- Optimized for Anchor framework projects
- Requires `programs/*/src` directory structure
- DeFi pattern matching is heuristic-based

---

## 中文

### 概述

RustGraph 是一个专为 Rust 项目设计的综合静态分析工具包，特别针对 Solana/Anchor 区块链开发进行了优化。它提供两个强大的工具：

1. **函数调用分析器**: 使用 rust-analyzer 提取和分析函数调用关系
2. **Solana 结构体提取器**: 为 AI 漏洞分析提取完整的合约结构

### 主要特性

#### 函数调用分析器
- **🔍 全面的函数发现**: 自动发现整个 Rust 项目中的所有函数
- **📊 调用关系分析**: 分析调用者-被调用者关系，提供精确的源码位置信息
- **🎯 智能过滤**: 智能过滤外部依赖，专注于项目代码
- **📝 详细输出**: 生成包含文件路径和行号的可读文本报告
- **⚡ 快速分析**: 基于 rust-analyzer 强大的语义分析引擎构建

#### Solana 结构体提取器
- **🏗️ 完整结构提取**: 提取包含所有字段和约束的完整结构体定义
- **🔐 安全导向**: 专为 AI 漏洞扫描和安全审计设计
- **🎯 DeFi 协议支持**: 专门提取 DeFi 相关结构（预言机、池、借贷、金库、治理）
- **📋 完整上下文**: 提供完整上下文以防止跨文件误判
- **🚀 健壮解析**: 使用先进的括号匹配算法进行精确提取

### 工具介绍

#### 1. 函数调用分析器

利用 rust-analyzer 的语义分析能力：

1. **加载项目**: 发现并加载 Rust 项目工作空间
2. **提取函数**: 遍历所有模块和 impl 块以查找函数定义
3. **分析调用**: 使用 rust-analyzer 的调用层次 API 识别函数调用
4. **过滤结果**: 移除外部库调用，专注于项目内部关系
5. **生成报告**: 输出详细的调用关系信息

#### 2. Solana 结构体提取器

专为 Solana/Anchor 项目设计的工具：

1. **发现结构**: 查找所有带有 `#[account]` 和其他属性的结构体定义
2. **提取完整字段**: 使用健壮的括号匹配提取所有结构体字段
3. **捕获约束**: 提取账户约束和验证逻辑
4. **识别 DeFi 组件**: 识别预言机、池、借贷、金库和治理模式
5. **生成上下文**: 输出完整的 Rust 代码供 AI 分析

### 安装

#### 前置要求

- Rust 1.88+
- Cargo
- Python 3.7+（用于 Solana 结构体提取器）

#### 从源码构建

```bash
# 克隆仓库
git clone <repository-url>
cd rustgraph

# 构建函数分析器
cargo build --release

# Solana 提取器已准备就绪（Python 脚本）
```

### 使用方法

#### 函数调用分析器

```bash
# 分析当前目录
./target/release/rust-analyzer function-analyzer .

# 分析特定项目路径
./target/release/rust-analyzer function-analyzer /path/to/your/rust/project

# 保存输出到文件
./target/release/rust-analyzer function-analyzer /path/to/project --output call_graph.txt
```

#### Solana 结构体提取器

```bash
# 从 Solana 项目提取结构
python3 call-graph/solana_extractor_v3.py /path/to/solana/project

# 指定输出文件
python3 call-graph/solana_extractor_v3.py /path/to/solana/project --output extracted_structures.rs

# pump-science 项目示例
python3 call-graph/solana_extractor_v3.py ./2025-01-pump-science --output output/complete_structures.rs
```

### 输出格式

#### 函数调用分析器输出

```
# Function Call Hierarchy Analysis
# Format: caller_function -> callee_function (call_site)

src/lib.rs:15:initialize -> src/config.rs:23:load_config (call at 18:5)
src/lib.rs:15:initialize -> src/utils.rs:45:setup_logging (call at 19:5)
src/processor.rs:67:process_instruction -> src/state.rs:34:update_state (call at 72:9)
```

#### Solana 结构体提取器输出

```rust
// Extracted Solana Contract Structures for AI Vulnerability Analysis
// Complete context to prevent cross-file misanalysis

use anchor_lang::prelude::*;

// ===== PROGRAM IDs =====
declare_id!("EtZR9gh25YUM6LkL2o2yYV1KzyuDdftHvYk3wsb2Ypkj");

// ===== CONSTANTS =====
pub const BASIS_POINTS_DIVISOR: u64 = 10_000;

// ===== COMPLETE STRUCT DEFINITIONS =====
#[derive(InitSpace, Debug)]
#[account]
pub struct Global {
    pub initialized: bool,
    pub global_authority: Pubkey,
    pub migration_authority: Pubkey,
    pub migrate_fee_amount: u64,
    // ... 所有字段完整提取
}

// ===== GOVERNANCE =====
// Governance Type: admin
// Governance Type: migration
```

### 使用场景

#### 函数调用分析器
- **代码理解**: 快速理解大型代码库中的函数调用流程
- **依赖分析**: 识别哪些函数依赖于其他函数
- **重构支持**: 通过理解调用关系安全地进行重构
- **安全审计**: 追踪 Solana/Anchor 程序中的执行路径

#### Solana 结构体提取器
- **AI 漏洞扫描**: 为基于 AI 的安全分析提供完整上下文
- **安全审计**: 提取所有合约结构供手动审查
- **文档生成**: 生成全面的结构文档
- **跨文件分析**: 防止因结构体定义不完整导致的误判

### DeFi 协议支持

Solana 结构体提取器包含对以下协议的专门支持：

- **🔮 预言机集成**: Switchboard、Pyth、Chainlink 价格馈送
- **💧 流动性池**: 恒定乘积、稳定币交换、集中流动性
- **💰 借贷协议**: 抵押率、清算阈值、利率
- **🏦 金库策略**: 收益农场、借贷策略、质押池
- **🏛️ 治理机制**: 多签、DAO、时间锁机制

### 架构

#### 函数调用分析器组件
- **函数提取器**: 使用 HIR（高级中间表示）发现所有函数
- **调用分析器**: 使用 rust-analyzer 的调用层次 API 进行精确的调用检测
- **路径过滤器**: 智能过滤外部依赖
- **报告生成器**: 使用相对路径和可读格式格式化输出

#### Solana 结构体提取器组件
- **结构解析器**: 用于完整提取的健壮括号匹配算法
- **约束分析器**: 提取账户约束和验证逻辑
- **DeFi 模式匹配器**: 识别常见的 DeFi 协议模式
- **上下文生成器**: 输出完整的 Rust 代码供分析

### 限制

#### 函数调用分析器
- 仅分析静态函数调用（不分析动态分发）
- 需要包含 `Cargo.toml` 的有效 Rust 项目
- 大型项目可能需要时间分析

#### Solana 结构体提取器
- 针对 Anchor 框架项目优化
- 需要 `programs/*/src` 目录结构
- DeFi 模式匹配基于启发式算法

### 贡献

欢迎贡献！请查看我们的贡献指南了解更多信息。

### 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。