# Solana Analyzer

用于分析 Solana/Rust 项目的 Python 包（已发布至 PyPI），封装了对定制版 rust-analyzer 的调用，提供符号查找、结构体提取与调用图分析三大能力。

## 功能特性

- **符号查找**: 在 Rust 项目中查找特定符号（函数、结构体等）
- **结构体分析**: 提取合约结构体、常量、Program ID（返回汇总信息）
- **调用图分析**: 生成函数调用关系图并输出为 JSON 文件
- **多种使用方式**: 支持 Python API 与命令行工具

## 安装

### 方式 A：通过 PyPI（推荐，自动构建）

```bash
pip install solana-fcg-tool
```

- 当前版本：`1.0.3`
- 项目主页：`https://pypi.org/project/solana-fcg-tool/1.0.3/`

> **新特性**：从 v1.0.1 开始，pip install 会自动检测并安装 Rust 环境，然后构建定制版 rust-analyzer 二进制。无需手动配置！

**自动安装流程**：
1. 检测系统是否已安装 Rust/Cargo
2. 如未安装，自动下载并安装 Rust（Unix/Linux/macOS）
3. 自动构建定制版 rust-analyzer 二进制
4. 将二进制文件集成到 Python 包中

**系统要求**：
- **macOS/Linux**: 支持自动安装 Rust 和构建
- **Windows**: 需要手动安装 Rust（见下方说明）
- **网络连接**: 首次安装需要下载 Rust 工具链

**Windows 用户**：
如果您使用 Windows，请先手动安装 Rust：
1. 访问 https://rustup.rs/
2. 下载并运行 rustup-init.exe
3. 重启终端后再运行 `pip install solana-fcg-tool`

### 方式 B：本地开发模式

```bash
pip install -e .
```

## 二进制依赖（重要）

本工具需要一个包含自定义子命令的 rust-analyzer 可执行文件。你可以：

1) 在本仓库根目录构建二进制

```bash
cargo build --release
# 生成的二进制位于：target/release/rust-analyzer
```

2) 让工具能找到该二进制（任选其一）：

- 放到 PATH 中，例如：`cp target/release/rust-analyzer ~/.local/bin/`（或 `/usr/local/bin/`）
- 放到包目录：
  ```bash
  python - <<'PY'
  import solana_fcg_tool, pathlib
  p = pathlib.Path(solana_fcg_tool.__file__).parent / 'bin'
  p.mkdir(exist_ok=True)
  print(p)
  PY
  # 将上一步打印的路径替换到下面命令
  cp target/release/rust-analyzer <打印出的路径>/rust-analyzer
  ```
- 直接位于本仓库 `target/release/rust-analyzer`（开发模式下会自动发现）

> 提示：若使用系统 PATH 的 `rust-analyzer`，请确保该二进制就是本仓库构建出的定制版；官方发布版没有本工具需要的子命令。

## 快速开始

### 命令行（安装后提供 `solana-fcg-tool` 命令）

```bash
# 查找符号（逐行 JSON 输出）
solana-fcg-tool source-finder main /path/to/project

# 结构体分析（输出汇总信息到控制台）
solana-fcg-tool struct-analyzer /path/to/project

# 调用图分析（会在包目录 output 下生成 <project>_call_graph.json）
solana-fcg-tool call-graph /path/to/project
```

### Python API

```python
from solana_fcg_tool import SolanaAnalyzer

# 创建分析器实例
analyzer = SolanaAnalyzer("/path/to/your/rust/project")

# 符号查找：返回“多行 JSON 文本”（每行一个 JSON 对象）
symbols_text = analyzer.find_symbols("main")
print(symbols_text)

# 结构体分析：返回汇总字典（数量统计 + 文本摘要）
structs_summary = analyzer.analyze_structs()
print(structs_summary)

# 调用图分析：在包目录 output 中生成 <project>_call_graph.json
call_graph_info = analyzer.analyze_call_graph()
print(call_graph_info)
```

### 便捷函数

```python
from solana_fcg_tool import find_symbols, analyze_structs, analyze_call_graph

symbols_text = find_symbols("/path/to/project", "main")
structs_summary = analyze_structs("/path/to/project")
call_graph_info = analyze_call_graph("/path/to/project")
```

## 输出说明

- `source-finder`：标准输出为“逐行 JSON”，每行一个独立对象，表示一个符号命中；请按行解析。
- `struct-analyzer`：当前返回汇总信息（结构体/常量/ProgramID 数量与摘要），用于快速评估工程特征。
- `call-graph`：会在包目录 `solana_fcg_tool/output/` 下生成 `<project>_call_graph.json`，包含函数到被调函数的映射关系。

## 示例

仓库内置示例工程，可直接运行：

```bash
python example_usage.py

# 或者使用 CLI 对示例工程分析
solana-fcg-tool call-graph ./2025-01-pump-science
```

## 项目结构（简要）

```
├── solana_fcg_tool/          # Python 包源码与 CLI
│   ├── __init__.py           # API 导出（SolanaAnalyzer 及便捷函数）
│   ├── cli.py                # 命令行入口（console_script: solana-fcg-tool）
│   ├── interface.py          # 统一封装，查找并调用 rust-analyzer
│   └── output/               # 调用图 JSON 输出目录
├── crates/                   # 定制 rust-analyzer 源码（含子命令）
└── example_usage.py          # 使用示例
```

## 版本与依赖

- **Python**: >= 3.8
- **Rust/Cargo**: 构建定制版 rust-analyzer 必需
- **rust-analyzer（定制版）**: 含 `source-finder`/`function-analyzer` 子命令

## 故障排除（FAQ）

1. 找不到 `rust-analyzer` 或提示无子命令
   - 请使用本仓库 `cargo build --release` 构建的定制版，并放入 PATH 或包目录 `bin/` 下
   - 官方 rust-analyzer 不包含所需子命令
2. 提示“不是 Rust 工程”
   - 传入的路径需包含 `Cargo.toml`
3. 调用图分析失败
   - 检查二进制路径与权限：`chmod +x target/release/rust-analyzer`
   - 尝试在仓库根目录重新构建
4. Python 包已安装但 CLI 不可用
   - 确认 `solana-fcg-tool` 在 PATH 中：`which solana-fcg-tool`

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！