# Bathymesh Project - Copilot Instructions

IMPORTANT: use uv run to execute code with proper environment. e.g. uv run scripts/demo_v0_1.py

## Project Overview

Bathymesh is a Python-based workflow for converting maps, images, and gridded datasets into 3D printing meshes. The project aims to evolve from pure scripts → CLI tool → GUI application over time.

**Core Data Flow**: Input data → xarray format → NumPy arrays → 3D mesh output

## Project Goals

- Convert various geospatial/bathymetric data formats into 3D printable meshes
- Provide a clean, extensible pipeline for mesh generation
- Support multiple input formats (images, heightmaps, gridded datasets)
- Output STL and other mesh formats suitable for 3D printing
- Eventually integrate with slicing software (PrusaSlicer) for automated workflows

## Coding Standards

### Python Standards
- Follow PEP 8 strictly
- Use strict mypy typing for all functions and classes
- Include concise docstrings - make every word count
- Prefer class-based architecture for mesh operations
- Use standard logging library for all output
- Let library functions raise errors; handle them in runner scripts/UIs

### Project Structure
- `python/bathymesh/`: Core library code
- `scripts/`: Executable scripts and examples
- `data/`: Data storage (raw, interim, processed)
- Separate data processing logic from user interfaces

## Dependencies & Package Management

- **Package Manager**: UV for dependency management
- **Key Libraries**: 
  - Open3D (mesh operations)
  - NumPy (array processing)
  - xarray (data format standardization)
  - Shapely (geometric operations)
  - scikit-image (image processing)
  - triangle (triangulation)
- **Testing**: pytest
- No specific libraries to avoid - choose best tool for the task

## Architecture Preferences

### Code Organization
- Use class-based approach where appropriate. if something is a "thing", make it a class. if it can be just a function, make it a function.
- Python-first configuration (function/class parameters)
- Config file integration planned for later
- Functional decomposition within classes
- Type hints required for all public interfaces
- use dataclasses for simple data containers.
- if a function has more than 3 parameters, consider using a dataclass to group related parameters.
- keep these dataclassses in the same module as the class that uses them, unless they are used by multiple classes, in which case put them in a separate module called `data_structures.py`.
- use Enums for fixed sets of options, they are great! if needed, add methods to Enums for related functionality.

### Class Style

- All classes should have their attributes defined outside `__init__`
e.g.
```python
class MyClass:
    attribute: int
    def __init__(self, attribute: int):
        self.attribute = attribute
```
- put public methods before private methods
- if using a class, make the most its state. if a class has no state, it should probably be a function.
  - for example, instead of passing a triangulator to every function that needs it, make it an attribute of the class that uses it.
- use Union[T, None] as Optional[T]
- if a file has only one class, name the file after the class. e.g. `heightmap_processor.py` contains `HeightmapProcessor`

### Error Handling & Logging
- Use Python's standard `logging` library
- Library functions should raise appropriate exceptions
- Runner scripts and UIs handle error presentation to users
- Include debug information for complex mesh operations

### Data Processing
- Standardize on xarray for input data representation
- Convert to NumPy arrays for computational operations
- Support multiple input formats through xarray adapters
- Initial focus on small datasets; optimization for scale comes later

## Testing Strategy

- Use pytest for all testing
- Test data should be minimal but representative
- Focus on testing mesh generation pipeline components
- Include validation of mesh output quality

## Visualization & Output

- Be visualization-agnostic in core library
- Support multiple mesh output formats (STL primary target)
- Plan for future integration with visualization tools
- Future integration with PrusaSlicer for automated slicing
- Open3D visualization available but not required for core functionality

## Development Workflow

- Scripts in `scripts/` for experimentation and examples
- Core functionality in `python/bathymesh/` as reusable classes
- Incremental development: start simple, add complexity as needed
- Focus on clean interfaces between processing stages
- use uv run to execute code with proper environment

## Code Style Notes

- Prefer explicit over implicit
- Use descriptive variable names
- Keep functions focused on single responsibilities
- Document complex algorithms with inline comments
- Use type aliases for complex type signatures

## Current Development Phase

- Building core mesh generation pipeline
- Experimenting with different triangulation and extrusion approaches
- Testing with synthetic heightmap data
- Validating STL output quality for 3D printing
