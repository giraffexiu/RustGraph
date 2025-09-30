# RustGraph

A comprehensive static analysis toolkit for Rust projects, specifically optimized for Solana/Anchor blockchain development.

## Overview

RustGraph provides two main analysis capabilities:

1. **Rust Analyzer Extensions**: Enhanced rust-analyzer with function call analysis and symbol finding
2. **Solana Analyzer**: Python-based toolkit for Solana contract structure extraction and analysis

## Components

### 1. Rust Analyzer (Rust)

Enhanced rust-analyzer with additional analysis capabilities:

- **Function Call Analyzer**: Extracts function call relationships using semantic analysis
- **Symbol Finder**: Finds and extracts specific symbol definitions with detailed content

**Location**: `crates/rust-analyzer/`

### 2. Solana Analyzer (Python)

Python toolkit for Solana/Anchor project analysis:

- **Symbol Finder**: Find functions and structs in Rust projects
- **Struct Analyzer**: Extract complete Solana contract structures for AI vulnerability analysis
- **Call Graph Analyzer**: Analyze function call relationships

**Location**: `solana-analyzer/`

## Installation

### Prerequisites

- Rust 1.88+
- Cargo
- Python 3.7+

### Build Rust Analyzer

```bash
# Build the enhanced rust-analyzer
cargo build --release

# The binary will be available at:
# ./target/release/rust-analyzer
```

### Setup Solana Analyzer

```bash
# Navigate to solana-analyzer directory
cd solana-analyzer

# Install as library (optional)
pip install -e .
```

## Usage

### Rust Analyzer Extensions

#### Function Call Analysis
```bash
# Analyze function calls in a project
./target/release/rust-analyzer function-analyzer /path/to/rust/project

# Save output to file
./target/release/rust-analyzer function-analyzer /path/to/project --output call_graph.txt
```

#### Symbol Finding
```bash
# Find a specific function
./target/release/rust-analyzer symbol-finder function my_function_name

# Find a specific struct
./target/release/rust-analyzer symbol-finder struct MyStruct

# Search in specific project
./target/release/rust-analyzer symbol-finder function initialize --project-path /path/to/project
```

### Solana Analyzer

#### Command Line Usage

```bash
# Navigate to solana-analyzer directory
cd solana-analyzer

# Symbol search
python cli.py symbol-finder function my_function /path/to/project

# Struct analysis (outputs .rs file)
python cli.py struct-analyzer /path/to/solana/project

# Call graph analysis
python cli.py call-graph /path/to/rust/project
```

#### Python Library Usage

```python
from solana_analyzer.interface import analyze_symbols, analyze_structs, analyze_call_graph

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

## Output Examples

### Function Call Analysis Output
```
# Function Call Hierarchy Analysis
src/lib.rs:15:initialize -> src/config.rs:23:load_config (call at 18:5)
src/lib.rs:15:initialize -> src/utils.rs:45:setup_logging (call at 19:5)
src/processor.rs:67:process_instruction -> src/state.rs:34:update_state (call at 72:9)
```

### Struct Analysis Output (.rs file)
```rust
// Extracted Solana Contract Structures for AI Vulnerability Analysis
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
}
```

### Symbol Search Output (JSON)
```json
{
    "symbols": [
        {
            "name": "initialize",
            "type": "function",
            "file_path": "src/lib.rs",
            "line_number": 42
        }
    ]
}
```

## Use Cases

- **Code Understanding**: Analyze function call flows in large Rust codebases
- **Security Auditing**: Extract complete contract structures for vulnerability analysis
- **Refactoring Support**: Understand call relationships before making changes
- **AI Analysis**: Provide complete context for AI-based security scanning
- **Documentation**: Generate comprehensive structure documentation

## Project Structure

```
RustGraph/
├── crates/                    # Enhanced rust-analyzer source
│   ├── rust-analyzer/         # Main analyzer binary
│   └── ...                    # Supporting crates
├── solana-analyzer/           # Python analysis toolkit
│   ├── cli.py                 # Command line interface
│   ├── interface.py           # Core analysis logic
│   ├── struct-anayzer.py      # Struct extraction
│   └── funcation-anayzer.py   # Call graph analysis
├── 2025-01-pump-science/      # Example Solana project
└── target/                    # Build output
```

## Limitations

- Rust analyzer requires valid Rust project with `Cargo.toml`
- Solana analyzer optimized for Anchor framework projects
- Large projects may require significant analysis time
- Static analysis only (no runtime behavior analysis)

## License

MIT License