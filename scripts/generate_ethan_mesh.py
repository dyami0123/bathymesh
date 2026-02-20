import logging
from pathlib import Path

import numpy as np
from bathy.config import *
from bathy.workflows.generate_mesh import generate_mesh
from bathy.viz.contours import contour_plot

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    project_name = "ethan_profile"

    data_dir = Path(__file__).parent.parent / "data"

    heightmap_path = data_dir / "processed" / f"{project_name}.npy"
    save_mesh_path = data_dir / "meshes" / f"{project_name}.stl"

    save_mesh_path.parent.mkdir(parents=True, exist_ok=True)
    
    
    target_dimensions_mm = (
        620,
        470
    )
    
    target_height_mm = 1
    n_layers = 15
    exterior_buffer_width = 20
    exterior_buffer_value = -1
    
    _heightmap_data = np.load(heightmap_path)
    heightmap_dimensions = _heightmap_data.shape
    heightmap_max = np.nanmax(_heightmap_data)
    heightmap_min = np.nanmin(_heightmap_data)
    heightmap_height = heightmap_max - heightmap_min
    
    
    x_scale_factor = target_dimensions_mm[0] / heightmap_dimensions[1]
    y_scale_factor = target_dimensions_mm[1] / heightmap_dimensions[0]
    z_scale_factor = target_height_mm / heightmap_height


    offset = heightmap_min * -1.0  # Offset to ensure all heights are positive

    thresholds = [x for x in np.linspace(-0.1, target_height_mm, n_layers)] 
    
    # Mesh parameters
    units = MeshUnits(
        units_x=x_scale_factor*-1,
        units_y=y_scale_factor,
        units_z=z_scale_factor,
    )

    base_height = 0.0  # Base height for mesh
    # calculate thickness based on n_layers and target height
    thickness = target_height_mm / n_layers
    layer_spacing = thickness  # Vertical spacing between levels

    create_visuals: bool = True
    
    config = MeshGenerationConfig(
        heightmap_processing=HeighmapProcessingConfig(
            exterior_buffer_value=exterior_buffer_value,
            exterior_buffer_width=exterior_buffer_width,
            data_offset=offset,
            mesh_units=units,
            base_height=base_height,
            layer_thickness=thickness,
            thresholds=thresholds,
        ),
        contour_extraction=ContourExtractionConfig(
            min_polygon_area=1e-10,
            simplify_tolerance=0.5,
            max_segments=10000,
            min_area_fraction=0.00001,
        ),
        mesh_combination=MeshCombinationConfig(
            merge_threshold=1e-6,
        ),
        triangulation=TriangulationConfig(
            triangulator_add_interior_points=False,
            triangulator_interior_point_density=1.0,
        ),
        post_processing=PostProcessingConfig(
            apply_post_processing=True,
            remove_degenerate_triangles=True,
            remove_duplicated_vertices=True,
            remove_duplicated_triangles=True,
            remove_unreferenced_vertices=True,
            merge_close_vertices=True,
            merge_vertices_threshold=1e-6,
            target_triangle_count=100000,
            voxel_size=0.05,
        ),
        heightmap_splitting=HeightmapSplittingConfig(
            enabled=True,
            splits_x=[210,420,630],
            splits_y=[240],
        ),
        stateless=not create_visuals
    )

    _, generator = generate_mesh(
        heightmap_path,
        config=config,
        save_path=save_mesh_path
    )

    if create_visuals:
        save_path = data_dir / "processed" / f"{project_name}_contours.png"
        contour_plot(generator=generator, save_path=save_path, vmax=target_height_mm)
