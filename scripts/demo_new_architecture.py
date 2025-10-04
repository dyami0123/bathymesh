"""Example demonstrating the new heightmap-based mesh generation architecture."""

import numpy as np
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_new_architecture():
    """Demonstrate the new HeightmapHandler-based mesh generation."""
    
    # Import the new classes
    from python.bathymesh.core import (
        HeightmapHandler, 
        HeightmapProcessor,
        MeshCombiner,
        BaseMeshGenerator,
        FlatMeshGenerator, 
        ExtrudedMeshGenerator, 
        HeightmapMeshGenerator
    )
    from python.bathymesh.triangulation import BaseTriangulator, TriangleTriangulator
    from python.bathymesh.data_structures import MeshScaling
    from python.bathymesh.io import export_mesh
    
    logger.info("Creating synthetic heightmap data...")
    
    # Create a simple synthetic heightmap (40x40 grid)
    size = 40
    x = np.linspace(-2, 2, size)
    y = np.linspace(-2, 2, size)
    X, Y = np.meshgrid(x, y)
    
    # Create a heightmap with some interesting features
    heightmap = (
        0.5 * np.exp(-(X**2 + Y**2)) +  # Central peak
        0.3 * np.sin(3 * X) * np.cos(3 * Y) +  # Ripples
        0.1 * np.random.normal(0, 1, (size, size))  # Noise
    )
    
    # Set up scaling
    scaling = MeshScaling(scale_x=0.1, scale_y=0.1, scale_z=2.0)
    
    # Create heightmap handler
    heightmap_handler = HeightmapHandler(
        heightmap=heightmap,
        x_coords=x,
        y_coords=y,
        scaling=scaling
    )
    
    logger.info("Heightmap statistics:")
    stats = heightmap_handler.get_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    # Set up processors and generators
    triangulator: BaseTriangulator = TriangleTriangulator(quality_mesh=True)
    heightmap_processor = HeightmapProcessor()
    mesh_combiner = MeshCombiner()
    
    # Create different types of meshes
    logger.info("Creating flat mesh...")
    flat_generator: BaseMeshGenerator = FlatMeshGenerator(triangulator, heightmap_processor, mesh_combiner)
    flat_mesh = flat_generator.generate_mesh(heightmap_handler, height=0.0)
    logger.info(f"Flat mesh: {len(flat_mesh.vertices)} vertices, {len(flat_mesh.triangles)} triangles")
    
    logger.info("Creating extruded mesh...")
    extruded_generator: BaseMeshGenerator = ExtrudedMeshGenerator(triangulator, heightmap_processor, mesh_combiner)
    extruded_mesh = extruded_generator.generate_mesh(
        heightmap_handler, 
        base_height=-0.5, 
        thickness=1.0
    )
    logger.info(f"Extruded mesh: {len(extruded_mesh.vertices)} vertices, {len(extruded_mesh.triangles)} triangles")
    
    logger.info("Creating heightmap surface mesh...")
    heightmap_generator: BaseMeshGenerator = HeightmapMeshGenerator(triangulator, heightmap_processor, mesh_combiner)
    surface_mesh = heightmap_generator.generate_mesh(
        heightmap_handler,
        base_height=0.0,
        use_surface_mesh=True
    )
    logger.info(f"Surface mesh: {len(surface_mesh.vertices)} vertices, {len(surface_mesh.triangles)} triangles")
    
    logger.info("Creating contour-based heightmap mesh...")
    contour_mesh = heightmap_generator.generate_mesh(
        heightmap_handler,
        base_height=0.0,
        use_contours=True,
        threshold=0.2  # Use heightmap values above 0.2
    )
    logger.info(f"Contour mesh: {len(contour_mesh.vertices)} vertices, {len(contour_mesh.triangles)} triangles")
    
    # Export meshes to data/processed
    output_dir = Path("data/processed")
    output_dir.mkdir(exist_ok=True)
    
    logger.info("Exporting meshes...")
    try:
        export_mesh(flat_mesh, output_dir / "demo_flat_mesh.stl")
        export_mesh(extruded_mesh, output_dir / "demo_extruded_mesh.stl")
        export_mesh(surface_mesh, output_dir / "demo_surface_mesh.stl")
        export_mesh(contour_mesh, output_dir / "demo_contour_mesh.stl")
        logger.info(f"Meshes exported to {output_dir}")
    except Exception as e:
        logger.warning(f"Export failed: {e}")
    
    logger.info("Demo completed successfully! 🎉")

if __name__ == "__main__":
    demo_new_architecture()
