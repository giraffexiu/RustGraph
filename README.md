# Rust Call Graph Analyzer

A comprehensive tool for analyzing Rust project call hierarchies and generating detailed JSON output.

## Features

- **Call Hierarchy Analysis**: Analyze function call relationships in Rust projects
- **JSON Output**: Generate structured JSON data with call graph information
- **Python Library**: Easy-to-use Python library interface
- **Command Line Tool**: Convenient CLI for direct usage
- **Rust-Analyzer Integration**: Built on top of rust-analyzer for accurate analysis

## Installation

### Direct Usage

```python
# Add the rust_call_graph directory to your Python path
import sys
sys.path.append('/path/to/RustGraph')

from rust_call_graph import analyze_project
```

## Usage

### Python Library

```python
from rust_call_graph import analyze_project

# Analyze a Rust project
result = analyze_project("/path/to/rust/project")

if result.success:
    print(f"Analysis completed! Found {result.function_count} functions")
    print(f"Output saved to: {result.output_file}")
    
    # Access the raw data
    functions = result.data['functions']
    for func_id, func_info in functions.items():
        print(f"Function: {func_info['name']} at {func_info['file_path']}:{func_info['line']}")
        print(f"  Calls {func_info['call_count']} functions")
else:
    print(f"Analysis failed: {result.error}")
```

### Advanced Usage

```python
from rust_call_graph import RustCallGraphAnalyzer

# Create analyzer with custom settings
analyzer = RustCallGraphAnalyzer(rust_analyzer_path="/custom/path/to/rust-analyzer")

# Analyze with custom output directory and project name
result = analyzer.analyze(
    project_path="/path/to/rust/project",
    output_dir="/custom/output/dir",
    project_name="my_project"
)
```



## Output Format

The generated JSON file contains detailed call graph information:

```json
{
  "functions": {
    "file_path:line:function_name": {
      "file_path": "src/main.rs",
      "line": 10,
      "name": "main",
      "call_count": 3,
      "calls": [
        "src/lib.rs:20:helper_function",
        "src/utils.rs:15:utility_function",
        "src/lib.rs:30:another_function"
      ]
    }
  }
}
```

### Field Descriptions

- `file_path`: Path to the source file containing the function
- `line`: Line number where the function is defined
- `name`: Function name
- `call_count`: Total number of function calls made by this function
- `calls`: List of function IDs that this function calls (may contain duplicates)

## Project Structure

```
RustGraph/
├── rust_call_graph/          # Python library
│   ├── __init__.py           # Library entry point
│   ├── analyzer.py           # Main analyzer class
│   └── core.py              # Core processing logic
├── call-graph/              # Original scripts (legacy)
│   ├── analyze_project.py
│   ├── json_processor.py
│   └── output/
└── crates/                  # Rust analyzer source code
    └── rust-analyzer/
```

## Development

### Building from Source

```bash
# Build rust-analyzer
cargo build --release
```

### Legacy Scripts

The original analysis scripts are still available in the `call-graph/` directory:

```bash
# Using the original Python script
python call-graph/analyze_project.py /path/to/rust/project

# Using the shell script
./call-graph/call_graph_launcher.sh /path/to/rust/project
```

## Requirements

- Python 3.7+
- Rust toolchain (for building rust-analyzer)
- networkx library (install with: `pip install networkx>=2.5`)
- Rust project must contain a `Cargo.toml` file
- Project must be compilable (rust-analyzer needs to understand the code structure)
- Sufficient disk space for temporary files during analysis

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.