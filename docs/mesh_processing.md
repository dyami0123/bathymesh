# Mesh Processing Documentation

## Overview

The `MeshProcessor` class provides mesh cleanup, validation, and simplification operations while preserving sharp edges. It's designed to clean up meshes generated from heightmaps without smoothing that would blur important features.

## Key Features

### 1. Basic Cleanup Operations
- **Remove degenerate triangles**: Eliminates zero-area triangles
- **Remove duplicated vertices**: Removes exact vertex duplicates
- **Remove duplicated triangles**: Removes duplicate faces
- **Remove unreferenced vertices**: Cleans up unused vertices
- **Merge close vertices**: Merges vertices within a threshold

### 2. Simplification Methods
- **None**: No simplification, only cleanup
- **Vertex Clustering**: Voxel-based simplification (fast, good for large reductions)
- **Quadric Decimation**: Edge collapse simplification (slower, better quality)

## Usage

### Basic Usage with Workflow

```python
from bathymesh.workflows import MultiLevelMeshGenerationWorkflow, MultiLevelMeshConfig
from bathymesh.core import MeshProcessingConfig, SimplificationMethod
from bathymesh.data_structures import MeshType

# Configure mesh processing
processing_config = MeshProcessingConfig(
    remove_degenerate_triangles=True,
    remove_duplicated_vertices=True,
    remove_duplicated_triangles=True,
    remove_unreferenced_vertices=True,
    merge_close_vertices=True,
    merge_vertices_threshold=1e-6,
    simplification_method=SimplificationMethod.QUADRIC_DECIMATION,
    target_triangle_count=50000,
    verbose=True
)

# Create workflow with processing enabled
config = MultiLevelMeshConfig(
    thresholds=[0.2, 0.4, 0.6, 0.8],
    mesh_type=MeshType.EXTRUDED,
    thickness=0.5,
    process_mesh=True,
    processing_config=processing_config,
    save_output=True,
    output_path="output/processed_mesh.stl"
)

workflow = MultiLevelMeshGenerationWorkflow(config)
result = workflow.execute(heightmap)
```

### Direct Mesh Processing

```python
from bathymesh.core import MeshProcessor, MeshProcessingConfig, SimplificationMethod
import open3d as o3d

# Load or create a mesh
mesh = o3d.io.read_triangle_mesh("input.stl")

# Option 1: Quick cleanup with defaults
clean_mesh = MeshProcessor.quick_cleanup(mesh)

# Option 2: Custom processing
config = MeshProcessingConfig(
    simplification_method=SimplificationMethod.QUADRIC_DECIMATION,
    target_triangle_count=10000,
    verbose=True
)
processor = MeshProcessor(config)
processed_mesh = processor.process_mesh(mesh)

# Option 3: Just simplification
simplified_mesh = MeshProcessor.simplify(
    mesh,
    method=SimplificationMethod.VERTEX_CLUSTERING,
    voxel_size=0.05
)
```

## Configuration Options

### MeshProcessingConfig

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `remove_degenerate_triangles` | bool | True | Remove zero-area triangles |
| `remove_duplicated_vertices` | bool | True | Remove exact duplicate vertices |
| `remove_duplicated_triangles` | bool | True | Remove duplicate faces |
| `remove_unreferenced_vertices` | bool | True | Remove unused vertices |
| `merge_close_vertices` | bool | False | Merge vertices within threshold |
| `merge_vertices_threshold` | float | 1e-6 | Distance threshold for merging |
| `simplification_method` | SimplificationMethod | NONE | Simplification method to use |
| `target_triangle_count` | int | 100000 | Target for quadric decimation |
| `voxel_size` | float | 0.05 | Voxel size for vertex clustering |
| `verbose` | bool | True | Enable logging output |

## Simplification Methods Comparison

### None (Cleanup Only)
- **Speed**: Fast
- **Quality**: Original geometry preserved
- **Use case**: When you just need cleanup, no size reduction

### Vertex Clustering
- **Speed**: Very fast
- **Quality**: Good for large reductions
- **Use case**: Large meshes that need aggressive simplification
- **Control**: `voxel_size` parameter (larger = more simplification)

### Quadric Decimation
- **Speed**: Slower
- **Quality**: Better preservation of shape and features
- **Use case**: When quality is important
- **Control**: `target_triangle_count` parameter

## Integration with Workflows

Processing is integrated into both workflow types:

### Simple Mesh Workflow
```python
from bathymesh.workflows import SimpleMeshGenerationWorkflow, SimpleMeshConfig

config = SimpleMeshConfig(
    mesh_type=MeshType.EXTRUDED,
    process_mesh=True,
    processing_config=processing_config  # Optional, uses defaults if None
)
```

### Multi-Level Mesh Workflow
```python
from bathymesh.workflows import MultiLevelMeshGenerationWorkflow, MultiLevelMeshConfig

config = MultiLevelMeshConfig(
    thresholds=[0.2, 0.4, 0.6, 0.8],
    process_mesh=True,
    processing_config=processing_config  # Optional, uses defaults if None
)
```

## Design Philosophy

The mesh processor is designed to:
1. **Preserve sharp edges** - No smoothing filters to maintain terrain features
2. **Clean up artifacts** - Remove degenerate and duplicate geometry
3. **Optimize for 3D printing** - Reduce file size while maintaining quality
4. **Be configurable** - Enable/disable individual operations as needed
5. **Provide feedback** - Verbose logging to understand what's happening

## Performance Tips

1. **For large meshes**: Use vertex clustering first, then quadric decimation if needed
2. **For quality**: Use only cleanup operations, skip simplification
3. **For file size**: Start with aggressive simplification, adjust as needed
4. **Merge threshold**: Keep small (1e-6) to avoid losing detail

## Examples

Run the demo script to see all features in action:

```bash
uv run scripts/demo_mesh_processing.py
```

This will generate four meshes showing different processing configurations:
- Basic cleanup only
- Cleanup + quadric decimation
- Cleanup + vertex clustering  
- No processing (for comparison)
