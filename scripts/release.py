#!/usr/bin/env python3
"""
Release script for solana-fcg-tool
This script helps with creating releases and managing versions
"""

import os
import sys
import re
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {cmd}")
        print(f"stdout: {result.stdout}")
        print(f"stderr: {result.stderr}")
        return False
    return True


def check_git_status():
    """Check if git working directory is clean"""
    result = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True)
    if result.stdout.strip():
        print("Git working directory is not clean. Please commit or stash changes.")
        return False
    return True


def update_version(version):
    """Update version in setup.py, package __init__.py, and pyproject.toml (if present)."""
    project_root = Path(__file__).parent.parent

    # Update setup.py (robust regex, independent of current value)
    setup_py = project_root / "setup.py"
    if setup_py.exists():
        content = setup_py.read_text()
        # Use \g<1>/\g<3> to avoid backreference + digits merging (e.g. \1 + "1.0.3" -> \11)
        new_content, n = re.subn(r'(version\s*=\s*")([^\"]+)(")', rf"\g<1>{version}\g<3>", content)
        if n > 0:
            setup_py.write_text(new_content)
            print(f"Updated version in setup.py to {version}")
        else:
            print("Warning: Could not update version in setup.py via regex.")

    # Update package __init__.py __version__
    init_py = project_root / "solana_fcg_tool" / "__init__.py"
    if init_py.exists():
        content = init_py.read_text()
        new_content, n = re.subn(r'(__version__\s*=\s*")([^\"]+)(")', rf"\g<1>{version}\g<3>", content)
        if n > 0:
            init_py.write_text(new_content)
            print(f"Updated __version__ in solana_fcg_tool/__init__.py to {version}")
        else:
            print("Warning: Could not update __version__ in __init__.py via regex.")

    # Update pyproject.toml (if it declares version)
    pyproject_toml = project_root / "pyproject.toml"
    if pyproject_toml.exists():
        content = pyproject_toml.read_text()
        new_content, n = re.subn(r'(^\s*version\s*=\s*")([^\"]+)(")', rf"\g<1>{version}\g<3>", content, flags=re.MULTILINE)
        if n > 0:
            pyproject_toml.write_text(new_content)
            print(f"Updated version in pyproject.toml to {version}")
        else:
            # Not all projects declare version in pyproject.toml; that's fine.
            print("Note: No version field updated in pyproject.toml (may be using setup.py only).")


def build_package():
    """Build the Python package"""
    print("Building Python package...")
    
    # Clean previous builds
    if not run_command("rm -rf build/ dist/ *.egg-info/"):
        return False
    
    # Build package
    if not run_command("python -m build"):
        return False
    
    print("Package built successfully!")
    return True


def create_git_tag(version):
    """Create and push git tag"""
    tag = f"v{version}"
    
    if not run_command(f"git add ."):
        return False
    
    if not run_command(f'git commit -m "Release {version}"'):
        return False
    
    if not run_command(f"git tag {tag}"):
        return False
    
    print(f"Created git tag: {tag}")
    return True


def push_to_github():
    """Push changes and tags to GitHub"""
    if not run_command("git push"):
        return False
    
    if not run_command("git push --tags"):
        return False
    
    print("Pushed to GitHub successfully!")
    return True


def main():
    parser = argparse.ArgumentParser(description="Release script for solana-fcg-tool")
    parser.add_argument("version", help="Version to release (e.g., 1.0.4)")
    parser.add_argument("--skip-git-check", action="store_true", help="Skip git status check")
    parser.add_argument("--skip-build", action="store_true", help="Skip building package")
    parser.add_argument("--skip-tag", action="store_true", help="Skip creating git tag")
    parser.add_argument("--skip-push", action="store_true", help="Skip pushing to GitHub")
    
    args = parser.parse_args()
    
    # Change to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print(f"Creating release {args.version}")
    
    # Check git status
    if not args.skip_git_check and not check_git_status():
        sys.exit(1)
    
    # Update version
    update_version(args.version)
    
    # Build package
    if not args.skip_build and not build_package():
        sys.exit(1)
    
    # Create git tag
    if not args.skip_tag and not create_git_tag(args.version):
        sys.exit(1)
    
    # Push to GitHub
    if not args.skip_push and not push_to_github():
        sys.exit(1)
    
    print(f"Release {args.version} completed successfully!")
    print("GitHub Actions will now build multi-platform binaries and publish to PyPI.")


if __name__ == "__main__":
    main()