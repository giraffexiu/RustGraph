import sys
from pathlib import Path
def example_basic_usage():
    try:
        # Import the package
        from solana_fcg_tool import SolanaAnalyzer
        
        # Use the sample project inside this repo for a quick smoke test
        project_path = str(Path(__file__).parent / "2025-01-pump-science")
        
        print(f"Analyzing project: {project_path}")
        
        # Create analyzer instance
        analyzer = SolanaAnalyzer(project_path)
        
        # Example 1: Find symbols
        print("\n1. Finding symbols...")
        result = analyzer.find_symbols("CreateEvent")
        print(f"Result: {result}")
        
        # Example 2: Analyze structs
        print("\n2. Analyzing structs...")
        result = analyzer.analyze_structs()
        print(f"Result: {result}")
        
        # Example 3: Analyze call graph
        print("\n3. Analyzing call graph...")
        result = analyzer.analyze_call_graph()
        print(f"Result: {result}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure the package is installed.")
        print("For TestPyPI: python -m pip install --index-url https://test.pypi.org/simple/ --no-deps solana-fcg-tool==1.0.0")
    except Exception as e:
        print(f"Error: {e}")


def example_convenience_functions():
    """Example using convenience functions"""
    print("\n" + "="*60)
    print("Convenience Functions Example")
    print("="*60)
    
    try:
        # Import convenience functions
        from solana_fcg_tool import find_symbols, analyze_structs, analyze_call_graph
        
        # Use the sample project so the command works out-of-the-box
        project_path = str(Path(__file__).parent / "2025-01-pump-science")
        
        print(f"Analyzing project: {project_path}")
        
        # Use convenience functions
        print("\n1. Using find_symbols function...")
        symbols = find_symbols(project_path, "main")
        print(f"Symbols: {symbols}")
        
        print("\n2. Using analyze_structs function...")
        structs = analyze_structs(project_path)
        print(f"Structs: {structs}")
        
        print("\n3. Using analyze_call_graph function...")
        call_graph = analyze_call_graph(project_path)
        print(f"Call graph: {call_graph}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure the package is installed: pip install -e .")
    except Exception as e:
        print(f"Error: {e}")


def example_cli_usage():
    """Example using CLI programmatically"""
    print("\n" + "="*60)
    print("CLI Usage Example")
    print("="*60)
    
    try:
        import subprocess
        import sys
        
        # Use the sample project so the example works out-of-the-box
        project_path = str(Path(__file__).parent / "2025-01-pump-science")
        
        print(f"Analyzing project: {project_path}")
        
        # Prefer CLI from .venv-testpypi if available (installed from TestPyPI)
        repo_root = Path(__file__).parent
        test_cli = repo_root / ".venv-testpypi" / "bin" / "solana-fcg-tool"
        cli = str(test_cli) if test_cli.exists() else "solana-fcg-tool"

        # Example CLI commands (struct-analyzer doesn't require rust-analyzer)
        commands = [
            [cli, "struct-analyzer", project_path],
            [cli, "source-finder", "main", project_path],
            [cli, "call-graph", project_path],
        ]
        
        for cmd in commands:
            print(f"\nRunning: {' '.join(cmd)}")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                print(f"Return code: {result.returncode}")
                if result.stdout:
                    print(f"Output: {result.stdout[:200]}...")
                if result.stderr:
                    print(f"Error: {result.stderr}")
            except subprocess.TimeoutExpired:
                print("Command timed out")
            except FileNotFoundError:
                print("Command not found. Make sure the package is installed.")
                print("For TestPyPI: python -m pip install --index-url https://test.pypi.org/simple/ --no-deps solana-fcg-tool==1.0.0")
            except Exception as e:
                print(f"Error: {e}")
        
    except Exception as e:
        print(f"Error: {e}")


def example_with_real_project():
    """Example with a real project (if available)"""
    print("\n" + "="*60)
    print("Real Project Example")
    print("="*60)
    
    # Try to find a real Rust project in common locations
    possible_projects = [
        Path.home() / "projects",
        Path.home() / "workspace", 
        Path.home() / "code",
        Path("/tmp"),
    ]
    
    rust_project = None
    for base_dir in possible_projects:
        if base_dir.exists():
            for item in base_dir.iterdir():
                if item.is_dir() and (item / "Cargo.toml").exists():
                    rust_project = item
                    break
            if rust_project:
                break
    
    if rust_project:
        print(f"Found Rust project: {rust_project}")
        
        try:
            from solana_fcg_tool import SolanaAnalyzer
            
            analyzer = SolanaAnalyzer(str(rust_project))
            
            # Try to analyze the real project
            print("\nAnalyzing real project...")
            result = analyzer.analyze_structs()
            print(f"Struct analysis result: {result}")
            
        except Exception as e:
            print(f"Error analyzing real project: {e}")
    else:
        print("No Rust projects found in common locations")
        print("To test with a real project, modify the project_path in the examples above")


def main():
    """Main function"""
    print("Solana Analyzer Package - Usage Examples")
    print("="*60)
    
    # Check if package is installed
    try:
        import solana_fcg_tool
        print(f"✓ Package is installed (version: {solana_fcg_tool.__version__})")
    except ImportError:
        print("✗ Package is not installed")
        print("Please run: pip install -e .")
        return
    
    # Run examples
    example_basic_usage()
    example_convenience_functions()
    example_cli_usage()
    example_with_real_project()
    
    print("\n" + "="*60)
    print("Examples completed!")
    print("="*60)
    print("\nTo use with your own projects:")
    print("1. Modify the project_path variables in the examples above")
    print("2. Make sure your project has a Cargo.toml file")
    print("3. Run the examples again")


if __name__ == "__main__":
    main()