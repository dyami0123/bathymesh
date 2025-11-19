import logging
from pathlib import Path

import numpy as np
from bathymesh.config import (
    MeshConfig,
    GenerationParams,
    ContourParams,
    CombinerParams,
    TriangulationParams,
    PostProcessParams,
)
from bathymesh.data_model import HeightmapData, MeshUnits
from bathymesh.mesh_post_processor import SimplificationMethod
from bathymesh.project import Project
from bathymesh.visualization import Visualizer
from bathymesh.workflows.generate_mesh import generate_mesh

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Initialize Project
    # Assuming script is in scripts/ and project root is parent of scripts/
    project_root = Path(__file__).parent.parent
    project = Project(project_root)
    visualizer = Visualizer(project.debug_dir)

    # Define paths using Project
    heightmap_path = project.get_processed_path("palau_heightmap_bathy.npy")
    save_mesh_path = project.get_mesh_path("palau_underwater_mesh.stl")

    # Load Data
    raw_heightmap_data = np.load(heightmap_path)

    exterior_buffer_width = 20
    exterior_buffer_value = 0.0
    offset = 110.0

    # Create Configuration
    thresholds = [float(x) for x in np.linspace(0, 209, 30)]
    
    config = MeshConfig(
        generation=GenerationParams(
            thresholds=thresholds,
            base_height=0.0,
            layer_thickness=0.5,
        ),
        contour=ContourParams(
            min_polygon_area=1e-2,
            simplify_tolerance=0.5,
            max_segments=3000,
            min_area_fraction=0.1,
        ),
        combiner=CombinerParams(
            merge_threshold=1e-6,
        ),
        triangulation=TriangulationParams(
            add_interior_points=True,
            interior_point_density=1.0,
        ),
        post_process=PostProcessParams(
            enabled=True,
            remove_degenerate_triangles=True,
            remove_duplicated_vertices=True,
            remove_duplicated_triangles=True,
            remove_unreferenced_vertices=True,
            merge_close_vertices=True,
            merge_vertices_threshold=1e-6,
            simplification_method=SimplificationMethod.NONE,
            target_triangle_count=100000,
            voxel_size=0.05,
        ),
    )

    # Save config for future use
    project.save_config(config, "palau_underwater_mesh")

    # Mesh parameters
    units = MeshUnits(
        units_x=0.2,
        units_y=0.2,
        units_z=1.6,
    )

    create_visuals: bool = True

    heightmap_data = HeightmapData(
        data=raw_heightmap_data,
        exterior_buffer_width=exterior_buffer_width,
        exterior_buffer_value=exterior_buffer_value,
        units=units,
        data_offset=offset,
    )

    heightmap_data.post_process()

    generated_mesh, generator = generate_mesh(
        heightmap_data=heightmap_data,
        config=config,
        save_path=save_mesh_path,
        stateless=not create_visuals,
    )

    if create_visuals:
        visualizer.plot_contours(
            generator.threshold_snapshots,
            title="Extracted Contours at Different Height Thresholds",
            filename="palau_contours.png",
        )
        
        # Also demonstrate stack visualization
        visualizer.plot_contour_stack(
            generator.threshold_snapshots,
            title="Contour Stack Visualization",
            filename="palau_contour_stack.png",
        )
