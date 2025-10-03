#!/usr/bin/env python3
"""Example script demonstrating bathymesh v0.1 library usage."""

import logging
import numpy as np
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the bathymesh library
try:
    from bathymesh import BathymeshWorkflow, create_test_heightmap
except ImportError:
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / "python"))
    from bathymesh import BathymeshWorkflow, create_test_heightmap


def main():
    """Demonstrate bathymesh library functionality."""
    logger.info("Starting bathymesh v0.1 demonstration")
    
    # Create workflow instance
    workflow = BathymeshWorkflow(
        min_polygon_area=1e-2,
        merge_threshold=1e-6,
        quality_triangulation=True
    )
    
    # Create test heightmap
    logger.info("Creating test heightmap...")
    heightmap = create_test_heightmap(
        width=50, 
        height=50, 
        feature_scale=10.0, 
        noise_level=0.1
    )
    
    logger.info(f"Heightmap shape: {heightmap.shape}, range: [{heightmap.min():.3f}, {heightmap.max():.3f}]")
    
    # 1. Create simple surface mesh
    logger.info("Creating simple surface mesh...")
    try:
        simple_mesh = workflow.create_simple_surface_mesh(
            heightmap,
            scale_x=1.0,
            scale_y=1.0, 
            scale_z=10.0,
            output_path="simple_heightmap_mesh_v0.1.stl"
        )
        
        mesh_info = workflow.get_mesh_info(simple_mesh)
        logger.info(f"Simple mesh: {mesh_info['num_vertices']} vertices, {mesh_info['num_triangles']} triangles")
        
    except Exception as e:
        logger.error(f"Failed to create simple surface mesh: {e}")
    
    # 2. Create flat contour mesh
    logger.info("Creating flat contour mesh...")
    try:
        thresholds = [1.0, 2.0, 3.0, 4.0]
        flat_mesh = workflow.create_contour_mesh(
            heightmap,
            thresholds=thresholds,
            thickness=1.0,
            extrude=False,
            output_path="flat_contour_mesh_v0.1.stl"
        )
        
        mesh_info = workflow.get_mesh_info(flat_mesh)
        logger.info(f"Flat contour mesh: {mesh_info['num_vertices']} vertices, {mesh_info['num_triangles']} triangles")
        
    except Exception as e:
        logger.error(f"Failed to create flat contour mesh: {e}")
    
    # 3. Create extruded contour mesh
    logger.info("Creating extruded contour mesh...")
    try:
        thresholds = [1.0, 2.0, 3.0, 4.0]
        extruded_mesh = workflow.create_contour_mesh(
            heightmap,
            thresholds=thresholds,
            thickness=0.2,
            extrude=True,
            output_path="extruded_contour_mesh_v0.1.stl"
        )
        
        mesh_info = workflow.get_mesh_info(extruded_mesh)
        logger.info(f"Extruded contour mesh: {mesh_info['num_vertices']} vertices, {mesh_info['num_triangles']} triangles")
        logger.info(f"Mesh is watertight: {mesh_info['is_watertight']}")
        
    except Exception as e:
        logger.error(f"Failed to create extruded contour mesh: {e}")
    
    logger.info("Bathymesh v0.1 demonstration completed!")


if __name__ == "__main__":
    main()
