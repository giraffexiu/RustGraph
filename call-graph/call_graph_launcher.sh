#!/bin/bash

# Project Call Hierarchy Analyzer
# This script integrates the Rust call hierarchy analysis with JSON output generation.

set -e  # Exit on any error

# Function to print usage
print_usage() {
    echo "Usage: $0 <project_path>"
    echo "Example: $0 /path/to/rust/project"
    echo ""
    echo "This script will:"
    echo "1. Build rust-analyzer if needed"
    echo "2. Run call hierarchy analysis on the project"
    echo "3. Generate JSON output with call relationship data"
}

# Check arguments
if [ $# -ne 1 ]; then
    print_usage
    exit 1
fi

PROJECT_PATH="$1"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RUST_ANALYZER_DIR="$(dirname "$SCRIPT_DIR")"

# Validate project path
if [ ! -d "$PROJECT_PATH" ]; then
    echo "Error: Project path '$PROJECT_PATH' does not exist."
    exit 1
fi

# Check if it's a Rust project
if [ ! -f "$PROJECT_PATH/Cargo.toml" ]; then
    echo "Error: '$PROJECT_PATH' does not appear to be a Rust project (no Cargo.toml found)."
    exit 1
fi

echo "Starting analysis of Rust project: $PROJECT_PATH"
echo "============================================================"

# Step 1: Build rust-analyzer
echo "Building rust-analyzer..."
cd "$RUST_ANALYZER_DIR"
if ! cargo build --release; then
    echo "Failed to build rust-analyzer"
    exit 1
fi

# Step 2: Run call graph analysis
echo "Analyzing project call graph..."
RUST_ANALYZER_BINARY="$RUST_ANALYZER_DIR/target/release/rust-analyzer"
TEMP_OUTPUT=$(mktemp /tmp/call_graph_XXXXXX.txt)

# Ensure cleanup on exit
trap "rm -f '$TEMP_OUTPUT'" EXIT

if ! "$RUST_ANALYZER_BINARY" function-analyzer \
    "$PROJECT_PATH" \
    --output "$TEMP_OUTPUT"; then
    echo "Call graph analysis failed"
    exit 1
fi

echo "Call graph analysis completed"

# Step 3: Generate JSON output
echo "Generating JSON analysis..."
cd "$SCRIPT_DIR"

# Extract project name from path for output file naming
PROJECT_NAME=$(basename "$PROJECT_PATH")

if ! python3 json_processor.py "$TEMP_OUTPUT" "$PROJECT_NAME"; then
    echo "JSON analysis failed"
    exit 1
fi

echo "============================================================"
echo "Analysis pipeline completed successfully!"

# Show the output file location
# The output filename is based on the project name
OUTPUT_FILE="$SCRIPT_DIR/output/${PROJECT_NAME}_call_graph.json"

if [ -f "$OUTPUT_FILE" ]; then
    echo "Final JSON output: $OUTPUT_FILE"
    FINAL_OUTPUT="$OUTPUT_FILE"
else
    echo "Warning: Output file not found. Checking output directory..."
    ls -la "$SCRIPT_DIR/output/"
    exit 1
fi

# Show basic statistics
FUNCTION_COUNT=$(python3 -c "
import json
with open('$FINAL_OUTPUT', 'r') as f:
    data = json.load(f)
    print(len(data.get('functions', {})))
" 2>/dev/null || echo "unknown")

echo "Total functions analyzed: $FUNCTION_COUNT"