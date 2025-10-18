#!/usr/bin/env python3
"""
Test runner script for bathymesh test suite.

This script provides convenient commands for running different types of tests.
"""

import sys
import subprocess
from pathlib import Path
import argparse


def run_command(cmd, description):
    """Run a command and handle output."""
    print(f"\n=== {description} ===")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Error running command: {e}")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Bathymesh test runner")
    parser.add_argument(
        "--type", 
        choices=["all", "unit", "integration", "fast", "coverage"],
        default="all",
        help="Type of tests to run"
    )
    parser.add_argument(
        "--module",
        help="Specific module to test (e.g., test_utils, test_workflow)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--parallel", "-p",
        action="store_true", 
        help="Run tests in parallel"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["uv", "run", "pytest"]
    
    if args.verbose:
        cmd.append("-v")
    
    if args.parallel:
        cmd.extend(["-n", "auto"])
    
    # Add test type filters
    if args.type == "unit":
        cmd.extend(["-m", "unit"])
    elif args.type == "integration":
        cmd.extend(["-m", "integration"])
    elif args.type == "fast":
        cmd.extend(["-m", "not slow"])
    elif args.type == "coverage":
        cmd.extend([
            "--cov=python/bathymesh",
            "--cov-report=html",
            "--cov-report=term-missing"
        ])
    
    # Add specific module if specified
    if args.module:
        if not args.module.startswith("test_"):
            args.module = f"test_{args.module}"
        cmd.append(f"tests/{args.module}.py")
    
    # Run tests
    success = run_command(cmd, f"Running {args.type} tests")
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
