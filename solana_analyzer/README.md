# Solana Analyzer

Unified Rust project analysis library with symbol finder, struct analyzer, and call graph analyzer.

## Features

- **Symbol Finder**: Find functions and structs in Rust projects
- **Struct Analyzer**: Extract Solana contract structures, constants, and program IDs
- **Call Graph Analyzer**: Analyze function call relationships
- **Unified Interface**: Consistent API and command line interface

## Installation

```bash
pip install -e .
```

## Usage

### Command Line

#### Symbol Finder
```bash
python cli.py symbol-finder function my_function /path/to/project
python cli.py symbol-finder struct MyStruct /path/to/project
```

#### Struct Analyzer
```bash
python cli.py struct-analyzer /path/to/solana/project
```

#### Call Graph Analyzer
```bash
python cli.py call-graph /path/to/rust/project
```

### As Library

```python
from interface import analyze_symbols, analyze_structs, analyze_call_graph

# Symbol search
result = analyze_symbols("/path/to/project", "function", "my_function")
if result.success:
    print(f"Found symbols: {result.data}")

# Struct analysis
result = analyze_structs("/path/to/solana/project")
if result.success:
    print(f"Extracted {len(result.data.get('structs', []))} structs")

# Call graph analysis
result = analyze_call_graph("/path/to/project")
if result.success:
    print(f"Analyzed {len(result.data.get('functions', {}))} functions")
```

### Advanced Configuration

```python
from interface import (
    RustProjectAnalyzer, AnalysisConfig, AnalyzerType, OutputFormat
)

config = AnalysisConfig(
    project_path="/path/to/project",
    analyzer_type=AnalyzerType.STRUCT_ANALYZER,
    output_format=OutputFormat.JSON,
    disable_build_scripts=True
)

analyzer = RustProjectAnalyzer()
result = analyzer.analyze(config)
```

## Output Formats

### Symbol Search Result
```json
{
    "symbols": [
        {
            "name": "my_function",
            "type": "function",
            "file_path": "src/lib.rs",
            "line_number": 42
        }
    ]
}
```

### Struct Analysis Result
```json
{
    "structs": [
        {
            "name": "MyStruct",
            "fields": ["field1", "field2"],
            "file_path": "src/lib.rs"
        }
    ],
    "constants": [...],
    "program_ids": [...]
}
```

### Call Graph Result
```json
{
    "functions": {
        "main": {
            "calls": ["helper_function"],
            "file_path": "src/main.rs"
        }
    }
}
```

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `project_path` | str | Required | Rust project path |
| `analyzer_type` | AnalyzerType | Required | Analyzer type |
| `output_format` | OutputFormat | JSON | Output format |
| `disable_build_scripts` | bool | False | Disable build scripts |
| `disable_proc_macros` | bool | False | Disable proc macros |

## License

MIT License