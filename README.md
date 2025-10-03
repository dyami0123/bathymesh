# Bathymesh

A Python library for converting maps, images, and gridded datasets into 3D printing meshes.

## Overview

Bathymesh provides a clean, extensible pipeline for generating 3D printable meshes from 2D heightmaps and bathymetric data. The core data flow is: **Input data → xarray format → NumPy arrays → 3D mesh output**.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/dyami0123/bathymesh.git
cd bathymesh

# Install with uv (recommended)
uv sync

# Or install with pip
pip install -e .
```

### Basic Usage

```python
from bathymesh import BathymeshWorkflow, GeometryUtils

# Create workflow
workflow = BathymeshWorkflow()

# Create test heightmap
heightmap = GeometryUtils.create_test_heightmap(width=50, height=50)

# Generate simple surface mesh
simple_mesh = workflow.create_simple_surface_mesh(
    heightmap, 
    scale_z=10.0,
    output_path="surface.stl"
)

# Generate contour-based mesh
contour_mesh = workflow.create_contour_mesh(
    heightmap,
    thresholds=[1.0, 2.0, 3.0, 4.0],
    thickness=0.2,
    extrude=True,
    output_path="contours.stl"
)
```

### Example Scripts

Run the demo to see all features:

```bash
python scripts/demo_v0_1.py
```

## Features

- **Simple Surface Meshes**: Direct conversion of heightmaps to 3D surface meshes
- **Contour-Based Meshes**: Extract contours at specified levels with optional extrusion
- **Multiple Export Formats**: STL, PLY, OBJ, OFF formats supported
- **Quality Triangulation**: Uses Triangle library for robust mesh generation
- **Extensible Architecture**: Clean class-based design for easy customization

## Architecture

Bathymesh v0.1 follows a modular architecture:

- `bathymesh.BathymeshWorkflow`: High-level API for common workflows
- `bathymesh.core.*`: Core processing classes (heightmaps, polygons, meshes)
- `bathymesh.triangulation.*`: Polygon triangulation utilities  
- `bathymesh.io.*`: Mesh export and I/O utilities
- `bathymesh.utils.*`: Geometric utility functions

See `ARCHITECTURE_V0_1.md` for detailed architecture documentation.

## Development Status

**Current Version**: v0.1.0 - Core library functionality

**Roadmap**:
- v0.2: CLI tool
- v0.3: Additional input formats (GeoTIFF, etc.)
- v0.4: GUI application
- v0.5: Integration with slicing software

## Dependencies

- Python 3.12+
- NumPy, Open3D, Shapely, scikit-image
- Triangle library for triangulation
- xarray for data format standardization

## Contributing

This project follows strict coding standards:
- PEP 8 compliance
- Type hints on all public interfaces
- Comprehensive docstrings
- Class-based architecture
- pytest for testing

## License

[Add your license information here]
