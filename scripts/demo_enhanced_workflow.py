"""Example demonstrating the enhanced BathymeshWorkflow with new mesh generation options."""

import numpy as np
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def demo_enhanced_workflow():
    """Demonstrate the enhanced BathymeshWorkflow with configurable mesh generation."""
    
    # Import the enhanced workflow
    from python.bathymesh import BathymeshWorkflow, MeshType, MeshScaling
    
    logger.info("Creating enhanced workflow demo...")
    
    # Create a more interesting synthetic heightmap (50x50 grid)
    size = 50
    x = np.linspace(-3, 3, size)
    y = np.linspace(-3, 3, size)
    X, Y = np.meshgrid(x, y)
    
    # Create a heightmap with multiple features
    heightmap = (
        1.0 * np.exp(-(X**2 + Y**2) / 2) +  # Central gaussian peak
        0.5 * np.exp(-((X - 1.5)**2 + (Y - 1.5)**2) / 0.5) +  # Secondary peak
        0.3 * np.sin(2 * np.pi * X / 2) * np.cos(2 * np.pi * Y / 2) +  # Wave pattern
        0.1 * np.random.normal(0, 1, (size, size))  # Noise
    )
    
    # Smooth the heightmap slightly
    from scipy.ndimage import gaussian_filter
    heightmap = gaussian_filter(heightmap, sigma=0.8)
    
    # Set up scaling for better proportions
    scaling = MeshScaling(scale_x=0.05, scale_y=0.05, scale_z=1.5)
    
    # Initialize workflow
    workflow = BathymeshWorkflow(
        min_polygon_area=1e-3,
        quality_triangulation=True
    )
    
    logger.info("Workflow initialized. Supported mesh types:")
    for mesh_type in workflow.get_supported_mesh_types():
        logger.info(f"  - {mesh_type}")
    
    # Create output directory
    output_dir = Path("data/processed/enhanced_workflow")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Heightmap stats: shape={heightmap.shape}, range=({heightmap.min():.3f}, {heightmap.max():.3f})")
    
    # Demonstrate different mesh types
    mesh_configs = [
        {
            "mesh_type": MeshType.SURFACE,
            "name": "surface_mesh",
            "description": "Direct surface mesh from heightmap",
            "params": {"base_height": 0.0}
        },
        {
            "mesh_type": MeshType.FLAT,
            "name": "flat_mesh",
            "description": "Flat mesh at specified height",
            "params": {"flat_height": 2.0}
        },
        {
            "mesh_type": MeshType.EXTRUDED,
            "name": "extruded_mesh",
            "description": "Extruded mesh from bounding polygon",
            "params": {"base_height": 0.0, "thickness": 1.0}
        },
        {
            "mesh_type": MeshType.CONTOUR,
            "name": "contour_mesh_high",
            "description": "Contour mesh at high threshold",
            "params": {"base_height": 0.0, "contour_threshold": 0.8}
        },
        {
            "mesh_type": MeshType.EXTRUDED,
            "name": "extruded_contour_mesh",
            "description": "Extruded mesh from contour extraction",
            "params": {
                "base_height": 0.0, 
                "thickness": 0.5, 
                "use_contours": True, 
                "contour_threshold": 0.6
            }
        }
    ]
    
    # Generate different mesh types
    for config in mesh_configs:
        logger.info(f"Creating {config['description']}...")
        
        try:
            mesh = workflow.create_mesh_from_heightmap(
                heightmap=heightmap,
                mesh_type=config["mesh_type"],
                scaling=scaling,
                output_path=output_dir / f"{config['name']}.stl",
                **config["params"]
            )
            
            # Get mesh info
            mesh_info = workflow.get_mesh_info(mesh)
            logger.info(f"  Created: {mesh_info.num_vertices} vertices, {mesh_info.num_triangles} triangles")
            
        except Exception as e:
            logger.error(f"Failed to create {config['name']}: {e}")
    
    # Demonstrate multi-level mesh generation
    logger.info("Creating multi-level meshes...")
    
    # Define height thresholds for multi-level generation
    thresholds = [0.2, 0.5, 0.8, 1.2]
    
    # Create multi-level extruded mesh
    multi_extruded = workflow.create_multi_level_mesh(
        heightmap=heightmap,
        thresholds=thresholds,
        mesh_type=MeshType.EXTRUDED,
        scaling=scaling,
        thickness=0.3,
        layer_spacing=0.4,
        output_path=output_dir / "multi_level_extruded.stl"
    )
    
    # Create multi-level flat mesh
    multi_flat = workflow.create_multi_level_mesh(
        heightmap=heightmap,
        thresholds=thresholds,
        mesh_type=MeshType.FLAT,
        scaling=scaling,
        thickness=0.2,
        layer_spacing=0.5,
        output_path=output_dir / "multi_level_flat.stl"
    )
    
    logger.info(f"Multi-level extruded: {len(multi_extruded.vertices)} vertices")
    logger.info(f"Multi-level flat: {len(multi_flat.vertices)} vertices")
    
    # Test legacy methods for backward compatibility
    logger.info("Testing legacy methods...")
    
    try:
        legacy_surface = workflow.create_simple_surface_mesh(
            heightmap, 
            scaling=scaling,
            output_path=output_dir / "legacy_surface.stl"
        )
        
        legacy_contour = workflow.create_contour_mesh(
            heightmap,
            thresholds=[0.3, 0.7, 1.1],
            thickness=0.4,
            extrude=True,
            output_path=output_dir / "legacy_contour.stl"
        )
        
        logger.info(f"Legacy surface: {len(legacy_surface.vertices)} vertices")
        logger.info(f"Legacy contour: {len(legacy_contour.vertices)} vertices")
        
    except Exception as e:
        logger.error(f"Legacy method failed: {e}")
    
    # Demonstrate HeightmapHandler usage
    logger.info("Testing direct HeightmapHandler usage...")
    
    heightmap_handler = workflow.create_heightmap_handler(
        heightmap=heightmap,
        scaling=scaling
    )
    
    logger.info(f"HeightmapHandler stats:")
    stats = heightmap_handler.get_stats()
    for key, value in stats.items():
        logger.info(f"  {key}: {value}")
    
    logger.info(f"All meshes exported to {output_dir}")
    logger.info("Enhanced workflow demo completed successfully! 🎉")

if __name__ == "__main__":
    demo_enhanced_workflow()
