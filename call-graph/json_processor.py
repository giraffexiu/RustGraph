import re
import json
import os
import sys
import networkx as nx
from typing import Dict, List
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class Function:
    """Function information"""
    file_path: str
    line: int
    name: str
    call_count: int = 0  # Total number of function calls made by this function
    calls: List[str] = None  # List of function names called by this function (duplicates allowed)
    
    def __post_init__(self):
        if self.calls is None:
            self.calls = []
    
    def get_id(self) -> str:
        return f"{self.file_path}:{self.line}:{self.name}"

class CallGraphAnalyzer:
    """Simplified call graph analyzer for JSON output only"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.functions: Dict[str, Function] = {}
    
    def parse_file(self, file_path: str) -> None:
        """Parse call relationship file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and ' -> ' in line:
                    self._parse_call_line(line)
    
    def _parse_call_line(self, line: str) -> None:
        """Parse single call relationship line"""
        # Match format: caller -> callee (call at line:column)
        pattern = r'^(.+?)\s*->\s*(.+?)\s*\(call at (\d+):(\d+)\)$'
        match = re.match(pattern, line)
        
        if not match:
            return  # Skip invalid lines
        
        caller_str, callee_str, _, _ = match.groups()
        
        caller = self._parse_function_info(caller_str.strip())
        callee = self._parse_function_info(callee_str.strip())
        
        if caller and callee:
            self._add_call_relationship(caller, callee)
    
    def _parse_function_info(self, func_str: str) -> Function:
        """Parse function information string"""
        # Match format: file_path:line:function_name
        pattern = r'^(.+?):(\d+):(.+)$'
        match = re.match(pattern, func_str)
        
        if not match:
            return None
        
        file_path, line, name = match.groups()
        return Function(file_path, int(line), name)
    
    def _add_call_relationship(self, caller: Function, callee: Function) -> None:
        """Add call relationship to graph"""
        caller_id = caller.get_id()
        callee_id = callee.get_id()
        
        # Add function info
        if caller_id not in self.functions:
            self.functions[caller_id] = caller
        if callee_id not in self.functions:
            self.functions[callee_id] = callee
        
        # Increment caller's call count
        self.functions[caller_id].call_count += 1
        
        # Record the function called by the caller (duplicates allowed)
        self.functions[caller_id].calls.append(callee_id)
        
        # Add edge to graph
        self.graph.add_edge(caller_id, callee_id)
    

    
    def to_json(self) -> str:
        """Convert call graph to JSON format"""
        # Build functions dictionary
        functions_dict = {}
        for func_id, func in self.functions.items():
            functions_dict[func_id] = {
                'file_path': func.file_path,
                'line': func.line,
                'name': func.name,
                'call_count': func.call_count,
                'calls': func.calls
            }
        
        # Build result
        result = {
            'functions': functions_dict
        }
        
        return json.dumps(result, indent=2, ensure_ascii=False)

def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print("Usage: python call_graph_analyzer.py <input_file> [project_name]")
        print("Example: python call_graph_analyzer.py ../temp_file.txt mango-v3")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    # Use provided project name if available, otherwise extract from input filename
    if len(sys.argv) == 3:
        project_name = sys.argv[2]
    else:
        input_basename = os.path.basename(input_file)
        project_name = os.path.splitext(input_basename)[0]
    
    # Generate output filename based on project name
    input_name = project_name
    
    # Create output directory if it doesn't exist
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, f"{input_name}_call_graph.json")
    
    analyzer = CallGraphAnalyzer()
    try:
        analyzer.parse_file(input_file)
        json_result = analyzer.to_json()
        
        # Write to JSON file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(json_result)
        
        print(f"Analysis complete. Results saved to: {output_file}")
        print(f"Total functions: {len(analyzer.functions)}")
        
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()