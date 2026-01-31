#!/bin/bash
# Pixi activation script for bathymesh development environment

echo "🐍 Bathymesh Development Environment (Pixi + UV)"
echo "Python version: $(python --version)"
echo "Location: $(which python)"
echo "UV version: $(uv --version)"
echo "Pixi version: $(pixi --version)"
echo ""
echo "Using Pixi for system dependencies + UV for Python packages"
echo ""
echo "Available commands:"
echo "  - pixi run install      (sync Python dependencies with uv)"
echo "  - pixi run test         (run all tests)"
echo "  - pixi run test-unit    (run unit tests only)"
echo "  - pixi run demo         (run demo script)"
echo "  - uv add <package>      (add new Python dependency)"
echo "  - uv run <script>       (run script with dependencies)"
echo ""

# Auto-sync dependencies if pyproject.toml exists
if [ -f "pyproject.toml" ]; then
  echo "Syncing Python dependencies with UV..."
  uv sync
  echo ""
fi

echo "✅ Environment ready! You can now work on your bathymesh project."
echo ""
