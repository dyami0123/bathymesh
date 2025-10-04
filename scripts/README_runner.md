# Bathymesh Runner Script

A simple, configurable script for generating 3D meshes from synthetic heightmaps.

## Quick Start

1. **Run with default settings:**
   ```bash
   uv run scripts/run_bathymesh.py
   ```

2. **Customize the configuration:**
   - Edit the configuration sections at the top of `run_bathymesh.py`
   - See `config_examples.py` for ready-to-use configurations

## Configuration Options

### Stage 1: Heightmap Generation
- **`size`**: Grid dimensions (e.g., 60 = 60x60 grid)
- **`x_range`, `y_range`**: Coordinate ranges for the heightmap
- **`features`**: Control different terrain features:
  - `central_peak`: Main gaussian peak amplitude
  - `secondary_peak`: Secondary peak amplitude  
  - `wave_pattern`: Sine wave pattern amplitude
  - `noise_level`: Random noise amount

### Stage 2: Mesh Generation
- **`type`**: Mesh type (`SURFACE`, `FLAT`, `EXTRUDED`, `CONTOUR`)
- **`scaling`**: Scale factors for X, Y, Z dimensions
- **`base_height`**: Base Z-coordinate for the mesh
- **`thickness`**: Thickness for extruded meshes
- **`use_contours`**: Extract contours instead of full polygon
- **`multi_level`**: Create terraced/layered meshes

### Stage 3: Output
- **`directory`**: Output folder (default: `data/processed`)
- **`filename`**: Base filename without extension
- **`format`**: File format (`stl`, `ply`, `obj`, `off`)

## Mesh Types

- **`SURFACE`**: Direct surface mesh from heightmap data
- **`FLAT`**: Flat mesh at specified height
- **`EXTRUDED`**: 3D extruded mesh with thickness
- **`CONTOUR`**: Mesh from height contour extraction

## Examples

### Simple Surface Mesh
```python
MESH_CONFIG = {
    "type": MeshType.SURFACE,
    "scaling": MeshScaling(scale_x=0.05, scale_y=0.05, scale_z=2.0),
    "base_height": 0.0
}
```

### Multi-Level Terrain
```python
MESH_CONFIG = {
    "type": MeshType.EXTRUDED,
    "multi_level": {
        "enabled": True,
        "thresholds": [0.3, 0.6, 1.0, 1.4],
        "layer_spacing": 0.4
    }
}
```

## Output

Generated meshes are saved to `data/processed/` by default. The script outputs:
- Mesh statistics (vertices, triangles)
- File location
- Generation status

## Tips

- Start with smaller grid sizes (30-60) for faster generation
- Use `SURFACE` type for direct heightmap representation
- Use `EXTRUDED` with `multi_level` for terraced landscapes
- Adjust `scaling.scale_z` to control height exaggeration
- Check `config_examples.py` for proven configurations
