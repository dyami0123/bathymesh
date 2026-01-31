# Bathymesh - Agent Development Guide

This guide provides essential information for AI coding agents working in the bathymesh repository.

## Project Overview

Bathymesh is a Python library for converting maps, images, and gridded datasets into 3D printing meshes.
**Core Data Flow**: Input data → xarray format → NumPy arrays → 3D mesh output

## Build, Lint & Test Commands

### Environment Setup

This project uses **pixi** for system dependencies (OpenGL, X11, etc.) and **uv** for Python package management.

```bash
# First time setup: Install system dependencies with pixi
pixi install

# Enter the pixi shell (provides system libs + Python + uv)
pixi shell

# Or run commands directly through pixi
pixi run <command>
```

### Package Management
```bash
# Install Python dependencies (via pixi task or directly)
pixi run install    # Recommended: runs 'uv sync' in pixi environment
# OR
uv sync            # If already in pixi shell

# Add new Python package
uv add <package>

# Run any Python script with proper environment
pixi run uv run <script.py>
pixi run demo      # Convenience task for demo script
```

### Testing
```bash
# Run all tests (using pixi tasks)
pixi run test

# Run specific test types
pixi run test-unit         # Unit tests only
pixi run test-integration  # Integration tests only
pixi run test-coverage     # With coverage report

# Or use uv directly (in pixi shell or with pixi run)
pixi run uv run pytest
pixi run uv run pytest tests/test_workflow.py
pixi run uv run pytest tests/test_workflow.py::TestBathymeshWorkflow::test_initialization_default

# Run tests by marker
pixi run uv run pytest -m unit
pixi run uv run pytest -m integration
pixi run uv run pytest -m "not slow"

# Using the test runner script
pixi run uv run python run_tests.py --type all
pixi run uv run python run_tests.py --module test_workflow
```

### Development
```bash
# Run example scripts
pixi run hawaii    # Convenience task for Hawaii mesh generation
pixi run uv run scripts/generate_hawaii_mesh.py
pixi run uv run main.py
```

## Project Structure

```
python/bathy/          # Core library code
  ├── config.py        # Configuration dataclasses
  ├── data_model.py    # Data structures
  ├── workflows/       # High-level workflow implementations
  ├── image_processing/# Image processing modules
  ├── ui/              # User interface components
  └── viz/             # Visualization utilities
scripts/               # Executable scripts and examples
tests/                 # Test suite
data/                  # Data storage (raw, interim, processed)
docs/                  # Documentation
```

## Code Style Guidelines

### Python Standards
- **PEP 8**: Follow strictly
- **Type Hints**: Required for all public functions and classes (strict mypy typing)
- **Python Version**: 3.12+ (requires-python = ">=3.12,<3.13")
- **Logging**: Use standard library `logging` for all output (not print statements)

### Import Organization
```python
# Standard library imports
import logging
from pathlib import Path
from typing import List, Tuple, Union, Optional

# Third-party imports
import numpy as np
import open3d as o3d
from shapely.geometry import Polygon

# Local imports
from bathy.config import MeshGenerationConfig
from bathy.data_model import HeightmapData, MeshData
```

### Class Structure
```python
class MyClass:
    """Concise docstring - make every word count."""
    
    # Define attributes outside __init__
    attribute: int
    optional_attr: Union[float, None]  # Use Union[T, None] not Optional[T]
    
    def __init__(self, attribute: int) -> None:
        self.attribute = attribute
        self.optional_attr = None
    
    # Public methods first
    def public_method(self) -> None:
        """Public method docstring."""
        pass
    
    # Private methods after
    def _private_method(self) -> None:
        """Private method docstring."""
        pass
    
    @classmethod
    def from_config(cls, config: MeshGenerationConfig) -> "MyClass":
        """Create instance from configuration."""
        return cls(attribute=config.some_value)
```

### Naming Conventions
- **Classes**: PascalCase (e.g., `MeshGenerator`, `HeightmapProcessor`)
- **Functions/Methods**: snake_case (e.g., `process_mesh`, `extract_contours`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `DEFAULT_THRESHOLD`)
- **Private methods**: Prefix with `_` (e.g., `_create_side_faces`)
- **File naming**: If file has only one class, name file after class in snake_case (e.g., `heightmap_processor.py` contains `HeightmapProcessor`)

### Dataclasses & Types
```python
from dataclasses import dataclass, field
from enum import Enum

# Use dataclasses for simple data containers
@dataclass
class MeshUnits:
    """Scaling parameters for mesh generation."""
    units_x: float = 1.0
    units_y: float = 1.0
    units_z: float = 1.0

# Use Enums for fixed sets of options
class MeshType(Enum):
    SURFACE = "surface"
    CONTOUR = "contour"
    EXTRUDED = "extruded"

# If function has >3 parameters, use dataclass to group related params
# Keep dataclasses in same module unless used by multiple classes
# Then put in separate data_structures.py module
```

### Error Handling
- Library functions should **raise appropriate exceptions** (ValueError, TypeError, etc.)
- Runner scripts and UIs handle error presentation to users
- Include debug information for complex mesh operations
- Handle edge cases: empty inputs, invalid data types, large datasets

### Docstrings
```python
def generate_mesh(
    self,
    heightmap_data: HeightmapData,
    threshold: float,
    base_height: float = 0.0,
) -> list[o3d.geometry.TriangleMesh]:
    """
    Generate an extruded 3D mesh from heightmap data.
    
    Args:
        heightmap_data: Input heightmap data container
        threshold: Height threshold for contour extraction
        base_height: Z-coordinate of the base (default: 0.0)
    
    Returns:
        List of Open3D TriangleMesh objects
    
    Raises:
        ValueError: If parameters are invalid or mesh generation fails
    """
```

## Architecture Patterns

### Class-based Design
- Use classes for "things", functions for operations
- If something has state, make it a class
- If it's stateless, consider making it a function
- Make the most of class state - store dependencies as attributes instead of passing them repeatedly

### Configuration
- Python-first configuration (function/class parameters)
- Use `from_config()` class methods for creating instances from config
- Config file integration planned for later phases

### Data Processing
- Standardize on xarray for input data representation
- Convert to NumPy arrays for computational operations
- Support multiple input formats through xarray adapters

## Testing Strategy

### Test Organization
- All tests in `tests/` directory
- Test files named `test_*.py`
- Test classes named `Test*`
- Test functions named `test_*`

### Test Markers
```python
import pytest

@pytest.mark.unit
def test_simple_function():
    """Unit test example."""
    pass

@pytest.mark.integration
def test_full_workflow():
    """Integration test example."""
    pass

@pytest.mark.slow
def test_large_dataset():
    """Slow test example."""
    pass
```

### Test Best Practices
- Test data should be minimal but representative
- Include test cases for critical paths
- Account for edge cases (empty inputs, invalid types, large datasets)
- Include comments for edge cases and expected behavior
- Use fixtures in `conftest.py` for shared test data

## Common Patterns to Follow

From `.github/copilot-instructions.md`:
- Prioritize readability and clarity
- Include explanations for algorithm-related code
- Write comments on "why" certain design decisions were made
- Prefer explicit over implicit
- Use descriptive variable names
- Keep functions focused on single responsibilities
- Document complex algorithms with inline comments
- Use type aliases for complex type signatures

## Development Workflow

1. Scripts in `scripts/` for experimentation and examples
2. Core functionality in `python/bathy/` as reusable classes
3. Incremental development: start simple, add complexity as needed
4. Focus on clean interfaces between processing stages
5. Always use `uv run` to execute code with proper environment

## Key Dependencies

- **Open3D**: Mesh operations
- **NumPy**: Array processing  
- **xarray**: Data format standardization
- **Shapely**: Geometric operations
- **scikit-image**: Image processing
- **triangle**: Triangulation
- **pytest**: Testing framework

Choose the best tool for each task - no libraries are explicitly avoided.
