# Rust Project Analyzer

统一的Rust项目分析库，整合了符号查找、结构体分析和调用图分析功能。

## 功能特性

- **符号查找**: 在Rust项目中查找函数、结构体等符号
- **结构体分析**: 提取Solana合约中的结构体、常量和程序ID
- **调用图分析**: 分析项目中的函数调用关系
- **统一接口**: 提供一致的API和命令行接口
- **可扩展输出**: 支持文件输出和程序化处理
- **灵活配置**: 支持多种配置选项和自定义参数

## 安装

### 作为库安装

```bash
pip install -e .
```

### 直接使用

```bash
# 克隆项目后直接使用
python analyzer_cli.py --help
```

## 使用方法

### 命令行使用

#### 符号查找

```bash
# 查找函数
python analyzer_cli.py symbol-finder function my_function --project-path /path/to/rust/project

# 查找结构体
python analyzer_cli.py symbol-finder struct MyStruct --project-path /path/to/rust/project

# 指定输出路径和格式
python analyzer_cli.py symbol-finder function my_function \
    --project-path /path/to/rust/project \
    --output-path result.json \
    --output-format json
```

#### 结构体分析

```bash
# 分析Solana合约结构体
python analyzer_cli.py struct-analyzer --project-path /path/to/solana/project

# 指定输出目录
python analyzer_cli.py struct-analyzer \
    --project-path /path/to/solana/project \
    --output-base-dir /path/to/output
```

#### 调用图分析

```bash
# 分析函数调用关系
python analyzer_cli.py call-graph --project-path /path/to/rust/project

# 详细输出
python analyzer_cli.py call-graph --project-path /path/to/rust/project --verbose
```

#### 通用选项

```bash
# 禁用构建脚本和过程宏
python analyzer_cli.py struct-analyzer \
    --project-path /path/to/project \
    --disable-build-scripts \
    --disable-proc-macros

# 指定过程宏服务器
python analyzer_cli.py symbol-finder function my_func \
    --project-path /path/to/project \
    --proc-macro-srv /path/to/proc-macro-srv
```

### 作为库使用

#### 基本使用

```python
from rust_analyzer import analyze_symbols, analyze_structs, analyze_call_graph

# 符号查找
result = analyze_symbols("/path/to/project", "function", "my_function")
if result.success:
    print(f"找到符号: {result.data}")
else:
    print(f"分析失败: {result.error_message}")

# 结构体分析
result = analyze_structs("/path/to/solana/project")
if result.success:
    structs = result.data.get("structs", [])
    print(f"找到 {len(structs)} 个结构体")

# 调用图分析
result = analyze_call_graph("/path/to/project")
if result.success:
    functions = result.data.get("functions", {})
    print(f"分析了 {len(functions)} 个函数")
```

#### 高级配置

```python
from rust_analyzer import (
    RustProjectAnalyzer, AnalysisConfig, AnalyzerType, OutputFormat,
    CallbackOutputHandler
)

# 创建自定义配置
config = AnalysisConfig(
    project_path="/path/to/project",
    analyzer_type=AnalyzerType.STRUCT_ANALYZER,
    output_format=OutputFormat.JSON,
    output_path="/path/to/output.json",
    disable_build_scripts=True,
    disable_proc_macros=True
)

# 执行分析
analyzer = RustProjectAnalyzer()
result = analyzer.analyze(config)
```

#### 自定义输出处理

```python
from rust_analyzer import analyze_structs, CallbackOutputHandler

# 定义自定义处理函数
def custom_handler(result):
    """自定义结果处理函数"""
    if result.success:
        structs = result.data.get("structs", [])
        print(f"处理 {len(structs)} 个结构体:")
        for struct in structs[:5]:  # 只显示前5个
            print(f"  - {struct.get('name', 'Unknown')}")
        
        # 可以进行进一步处理，如保存到数据库、发送到API等
        return {"processed_count": len(structs)}
    else:
        print(f"分析失败: {result.error_message}")
        return None

# 使用自定义处理器
result = analyze_structs(
    "/path/to/project",
    output_handler=custom_handler
)
```

#### 批量分析

```python
from rust_analyzer import RustProjectAnalyzer, AnalysisConfig, AnalyzerType

def analyze_multiple_projects(project_paths, analyzer_type=AnalyzerType.STRUCT_ANALYZER):
    """批量分析多个项目"""
    analyzer = RustProjectAnalyzer()
    results = []
    
    for project_path in project_paths:
        config = AnalysisConfig(
            project_path=project_path,
            analyzer_type=analyzer_type
        )
        result = analyzer.analyze(config)
        results.append({
            "project": project_path,
            "success": result.success,
            "data": result.data if result.success else None,
            "error": result.error_message if not result.success else None
        })
    
    return results

# 使用示例
projects = [
    "/path/to/project1",
    "/path/to/project2", 
    "/path/to/project3"
]

results = analyze_multiple_projects(projects)
for result in results:
    print(f"项目 {result['project']}: {'成功' if result['success'] else '失败'}")
```

## 输出格式

### JSON格式

所有分析器都支持JSON格式输出，结构如下：

```json
{
    "success": true,
    "analyzer_type": "struct_analyzer",
    "project_path": "/path/to/project",
    "execution_time": 2.34,
    "data": {
        // 具体的分析结果数据
    },
    "metadata": {
        "timestamp": "2024-01-01T12:00:00Z",
        "config": {
            // 分析配置信息
        }
    }
}
```

### 符号查找结果

```json
{
    "symbols": [
        {
            "name": "my_function",
            "type": "function",
            "file_path": "src/lib.rs",
            "line_number": 42,
            "content": "fn my_function() -> i32 { ... }"
        }
    ]
}
```

### 结构体分析结果

```json
{
    "structs": [
        {
            "name": "MyStruct",
            "fields": ["field1", "field2"],
            "file_path": "src/lib.rs",
            "line_number": 10
        }
    ],
    "constants": [
        {
            "name": "MY_CONSTANT",
            "value": "42",
            "file_path": "src/lib.rs"
        }
    ],
    "program_ids": [
        {
            "name": "PROGRAM_ID",
            "value": "11111111111111111111111111111111",
            "file_path": "src/lib.rs"
        }
    ]
}
```

### 调用图分析结果

```json
{
    "functions": {
        "main": {
            "calls": ["helper_function", "another_function"],
            "called_by": [],
            "file_path": "src/main.rs",
            "line_number": 5
        }
    }
}
```

## 配置选项

| 选项 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `project_path` | str | 必需 | Rust项目路径 |
| `analyzer_type` | AnalyzerType | 必需 | 分析器类型 |
| `output_format` | OutputFormat | JSON | 输出格式 |
| `output_path` | str | None | 输出文件路径 |
| `output_base_dir` | str | "./output" | 输出基础目录 |
| `disable_build_scripts` | bool | False | 禁用构建脚本 |
| `disable_proc_macros` | bool | False | 禁用过程宏 |
| `proc_macro_srv` | str | None | 过程宏服务器路径 |
| `symbol_type` | str | None | 符号类型（符号查找专用） |
| `symbol_name` | str | None | 符号名称（符号查找专用） |

## 错误处理

库提供了完善的错误处理机制：

```python
from rust_analyzer import analyze_structs

result = analyze_structs("/invalid/path")
if not result.success:
    print(f"分析失败: {result.error_message}")
    print(f"错误类型: {type(result.error_message)}")
    
    # 可以根据错误类型进行不同处理
    if "not found" in result.error_message.lower():
        print("项目路径不存在")
    elif "cargo.toml" in result.error_message.lower():
        print("不是有效的Rust项目")
```

## 扩展开发

### 添加新的分析器

```python
from rust_analyzer import BaseAnalyzer, AnalysisConfig, AnalysisResult

class CustomAnalyzer(BaseAnalyzer):
    def analyze(self, config: AnalysisConfig) -> AnalysisResult:
        # 实现自定义分析逻辑
        try:
            # 执行分析
            data = self._perform_analysis(config)
            
            return AnalysisResult(
                success=True,
                analyzer_type=config.analyzer_type,
                config=config,
                data=data
            )
        except Exception as e:
            return AnalysisResult(
                success=False,
                analyzer_type=config.analyzer_type,
                config=config,
                error_message=str(e)
            )
    
    def _perform_analysis(self, config: AnalysisConfig):
        # 具体的分析实现
        pass
```

### 自定义输出处理器

```python
from rust_analyzer import OutputHandler, AnalysisResult

class DatabaseOutputHandler(OutputHandler):
    def __init__(self, db_connection):
        self.db = db_connection
    
    def handle_output(self, result: AnalysisResult):
        if result.success:
            # 保存到数据库
            self.db.save_analysis_result(result)
            return {"saved": True, "id": result.id}
        else:
            # 记录错误日志
            self.db.log_error(result.error_message)
            return {"saved": False, "error": result.error_message}
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。

## 更新日志

### v1.0.0
- 初始版本
- 整合符号查找、结构体分析和调用图分析功能
- 提供统一的命令行和库接口
- 支持可扩展的输入输出处理