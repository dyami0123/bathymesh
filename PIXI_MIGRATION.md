# Migration from Nix to Pixi

This document describes the migration from Nix flake to Pixi for managing system dependencies.

## What Changed

### Package Management
- **Before**: Nix flake (`flake.nix`) for both system and Python dependencies
- **After**: Pixi (`pixi.toml`) for system dependencies + UV for Python packages

### Why Pixi?
- Cross-platform support (Linux, macOS Intel, macOS ARM)
- Faster than Nix on non-NixOS systems
- Better integration with conda-forge ecosystem
- Easier to use with UV for Python package management

## Quick Start

```bash
# Install system dependencies
pixi install

# Install Python dependencies
pixi run install

# Run tests
pixi run test

# Run demo
pixi run demo

# Enter shell with all dependencies
pixi shell
```

## Architecture

```
┌─────────────────────────────────────┐
│         Pixi Environment            │
│  ┌──────────────────────────────┐   │
│  │   System Dependencies        │   │
│  │  • OpenGL (mesa, libgl)      │   │
│  │  • X11 libraries             │   │
│  │  • C++ runtime               │   │
│  │  • Python 3.12               │   │
│  │  • UV package manager        │   │
│  └──────────────────────────────┘   │
│          ▼                           │
│  ┌──────────────────────────────┐   │
│  │   UV Environment (.venv)     │   │
│  │  • NumPy, Open3D, etc.       │   │
│  │  • All Python packages       │   │
│  └──────────────────────────────┘   │
└─────────────────────────────────────┘
```

## Files

- `pixi.toml` - Pixi configuration (system dependencies, tasks)
- `pixi-activation.sh` - Activation script that runs when entering pixi shell
- `pyproject.toml` - Python package configuration (unchanged)
- `.pixi/` - Pixi environment directory (gitignored)
- `pixi.lock` - Pixi lockfile (gitignored)

## Platform Support

### Linux (linux-64)
- Full OpenGL and X11 support
- All graphics libraries included
- Best for development with GUI tools

### macOS (osx-64, osx-arm64)
- Minimal system libraries (zlib, libffi, openssl)
- OpenGL provided by system
- May require Xcode Command Line Tools

## Tasks

Defined in `pixi.toml`:

```toml
[tasks]
install = "uv sync"                    # Install Python deps
test = "uv run pytest"                 # Run all tests
test-unit = "uv run pytest -m unit"    # Run unit tests
test-integration = "uv run pytest -m integration"
test-coverage = "uv run pytest --cov=..."
demo = "uv run scripts/demo_v0_1.py"
hawaii = "uv run scripts/generate_hawaii_mesh.py"
```

## Migration Checklist

- [x] Create `pixi.toml` with system dependencies
- [x] Create activation script
- [x] Update `.gitignore` for pixi files
- [x] Update `AGENTS.md` with new commands
- [x] Test pixi installation
- [x] Create `python/bathymesh/` wrapper package
- [ ] Update or fix tests that use `bathymesh` imports

## Known Issues

### Package Naming
The code is in the `bathy` module but some tests import `bathymesh`. A wrapper package `python/bathymesh/` has been created to bridge this gap, but tests may need updates.

### Test Compatibility
Some tests may expect classes (like `BathymeshWorkflow`) that don't exist in the current codebase. These tests need to be updated to match the current architecture.

## Troubleshooting

### Import errors
```bash
# Reinstall everything
pixi install
pixi run install

# Check if package is installed
pixi run uv run python -c "import bathy; print('OK')"
```

### OpenGL/GUI errors on Linux
```bash
# Make sure you're using pixi environment
pixi shell
# Then run your script
uv run your_script.py
```

### macOS-specific issues
```bash
# Install Xcode Command Line Tools if needed
xcode-select --install
```

## Keeping Nix (Optional)

The `flake.nix` file has been kept for reference and can still be used if needed:

```bash
# Using Nix (if you prefer)
nix develop

# Using Pixi (recommended)
pixi shell
```

## Next Steps

1. Remove `flake.nix` and `flake.lock` once pixi setup is confirmed working
2. Update CI/CD to use pixi
3. Update README.md with pixi installation instructions
4. Fix test imports to use correct module names
