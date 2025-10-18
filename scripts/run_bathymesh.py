#!/usr/bin/env python3
"""
Bathymesh Runner Script

A simple, configurable script for generating 3D meshes from heightmaps.
Modify the configuration section below to create different mesh types.
"""

import sys
import logging
from pathlib import Path
from typing import TYPE_CHECKING
import numpy as np
import subprocess

# Add bathymesh to path if running directly
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent / "python"))

from bathymesh import BathymeshWorkflow, MeshType, MeshScaling

if TYPE_CHECKING:
    import open3d as o3d

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION SECTION - Modify these settings to customize your mesh
# ============================================================================

# Stage 1: Heightmap Generation Configuration
HEIGHTMAP_CONFIG = {
    "size": 25,                    # Grid size (60x60)
    "x_range": (-1, 1),           # X coordinate range
    "y_range": (-1, 1),           # Y coordinate range
    "features": {
        "central_peak": 1.8,      # Central gaussian peak amplitude
        "secondary_peak": 0.,    # Secondary peak amplitude
        "wave_pattern": 0.,      # Sine wave pattern amplitude
        "noise_level": 0.05       # Random noise level
    }
}

# Stage 2: Mesh Generation Configuration
MESH_CONFIG = {
    "type": MeshType.EXTRUDED,     # Options: SURFACE, FLAT, EXTRUDED, CONTOUR
    "scaling": MeshScaling(
        scale_x=0.2,             # X-axis scaling factor
        scale_y=0.2,             # Y-axis scaling factor
        scale_z=1.6              # Z-axis (height) scaling factor
    ),
    "base_height": 0.0,           # Base height for mesh
    "thickness": 0.8,             # Thickness for extruded meshes
    "flat_height": 1.0,           # Height for flat meshes
    "use_contours": False,        # Extract contours instead of full polygon
    "contour_threshold": 0.5,     # Threshold for contour extraction
    
    # Multi-level mesh options (set thresholds to enable)
    "multi_level": {
        "enabled": True,         # Set to True for multi-level generation
        "thresholds": [0.8, 1.2],  # Height thresholds
        "layer_spacing": 0.4      # Vertical spacing between levels
    }
}

# Stage 3: Output Configuration
OUTPUT_CONFIG = {
    "directory": "data/processed", # Output directory
    "filename": "bathymesh_output",# Base filename (without extension)
    "format": "stl"                # File format: stl, ply, obj, off
}

# ============================================================================
# RUNNER IMPLEMENTATION - You probably don't need to modify below this line
# ============================================================================

def generate_heightmap(config: dict) -> np.ndarray:
    """Generate synthetic heightmap based on configuration."""
    logger.info("Stage 1: Generating heightmap...")
    
    size = config["size"]
    x_range = config["x_range"]
    y_range = config["y_range"]
    features = config["features"]
    
    # Create coordinate grids
    x = np.linspace(x_range[0], x_range[1], size)
    y = np.linspace(y_range[0], y_range[1], size)
    X, Y = np.meshgrid(x, y)
    
    # Build heightmap with configured features
    heightmap = np.zeros((size, size))
    
    # Central gaussian peak
    if features["central_peak"] > 0:
        heightmap += features["central_peak"] * np.exp(-(X**2 + Y**2) / 2)
    
    # Secondary peak (offset)
    if features["secondary_peak"] > 0:
        offset_x, offset_y = x_range[1] * 0.4, y_range[1] * 0.4
        heightmap += features["secondary_peak"] * np.exp(-((X - offset_x)**2 + (Y - offset_y)**2) / 0.5)
    
    # Wave pattern
    if features["wave_pattern"] > 0:
        heightmap += features["wave_pattern"] * np.sin(2 * np.pi * X / 2) * np.cos(2 * np.pi * Y / 2)
    
    # Add noise
    if features["noise_level"] > 0:
        heightmap += features["noise_level"] * np.random.normal(0, 1, (size, size))
    
    logger.info(f"  Generated {size}x{size} heightmap, range: ({heightmap.min():.3f}, {heightmap.max():.3f})")
    return heightmap

def generate_mesh(heightmap: np.ndarray, config: dict) -> 'o3d.geometry.TriangleMesh':
    """Generate mesh from heightmap based on configuration."""
    logger.info("Stage 2: Generating mesh...")
    
    # Initialize workflow
    workflow = BathymeshWorkflow(quality_triangulation=True)
    
    # Check if multi-level generation is enabled
    if config["multi_level"]["enabled"]:
        logger.info(f"  Creating multi-level {config['type'].value} mesh...")
        mesh = workflow.create_multi_level_mesh(
            heightmap=heightmap,
            thresholds=config["multi_level"]["thresholds"],
            mesh_type=config["type"],
            scaling=config["scaling"],
            base_height=config["base_height"],
            thickness=config["thickness"],
            layer_spacing=config["multi_level"]["layer_spacing"]
        )
    else:
        logger.info(f"  Creating {config['type'].value} mesh...")
        mesh = workflow.create_mesh_from_heightmap(
            heightmap=heightmap,
            mesh_type=config["type"],
            scaling=config["scaling"],
            base_height=config["base_height"],
            thickness=config["thickness"],
            flat_height=config["flat_height"],
            use_contours=config["use_contours"],
            contour_threshold=config["contour_threshold"] if config["use_contours"] else None
        )
    
    logger.info(f"  Generated mesh: {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles")
    return mesh

def save_output(mesh: 'o3d.geometry.TriangleMesh', config: dict) -> Path:
    """Save mesh to configured output location."""
    logger.info("Stage 3: Saving output...")
    
    # Create output directory
    output_dir = Path(config["directory"])
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Build filename
    filename = f"{config['filename']}.{config['format']}"
    output_path = output_dir / filename
    
    # Import export function
    from bathymesh import export_mesh
    
    # Save mesh
    export_mesh(mesh, output_path)
    logger.info(f"  Saved mesh to: {output_path}")
    
    return output_path

def main():
    """Main runner function."""
    logger.info("=== Bathymesh Runner ===")
    logger.info(f"Configuration: {MESH_CONFIG['type'].value} mesh, {HEIGHTMAP_CONFIG['size']}x{HEIGHTMAP_CONFIG['size']} heightmap")
    
    try:
        # Stage 1: Generate heightmap
        heightmap = generate_heightmap(HEIGHTMAP_CONFIG)
        
        # Stage 2: Generate mesh
        mesh = generate_mesh(heightmap, MESH_CONFIG)
        
        # Stage 3: Save output
        output_path = save_output(mesh, OUTPUT_CONFIG)
        
        logger.info("=== Completed Successfully! ===")
        logger.info(f"Output saved to: {output_path}")
        
        # Optionally, open the output file with the default viewer
        try:
            subprocess.run(['prusa-slicer', str(output_path)], check=True)
        except Exception as e:
            logger.warning(f"Failed to open output file with prusa-slicer: {e}")

    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
