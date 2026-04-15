import logging
from pathlib import Path

import numpy as np
from bathy.config import (
    ContourExtractionConfig,
    HeighmapProcessingConfig,
    MeshCombinationConfig,
    MeshGenerationConfig,
    MeshUnits,
    PostProcessingConfig,
    TriangulationConfig,
)
from bathy.workflows.generate_mesh import generate_mesh
from bathy.viz.contours import contour_plot

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    data_dir = Path(__file__).parent.parent / "data"

    heightmap_path = data_dir / "processed" / "hawaii_full.npy"
    save_mesh_path = data_dir / "meshes" / "hawaii.stl"

    save_mesh_path.parent.mkdir(parents=True, exist_ok=True)

    raw_heightmap_data = np.load(heightmap_path)

    exterior_buffer_width = 200
    exterior_buffer_value = -500
    offset = np.nanmin(raw_heightmap_data) * -1.1

    max_val = np.nanmax(raw_heightmap_data)

    # Mesh parameters
    units = MeshUnits(
        units_x=0.002,  # X-axis scaling factor
        units_y=0.002,  # Y-axis scaling factor
        units_z=1,  # Z-axis (height) scaling factor
    )

    thresholds = [
        x
        for x in np.linspace(
            exterior_buffer_value * 0.9,
            (offset + max_val),
            180,
        )
    ]  # Height thresholds

    base_height = 0.0  # Base height for mesh
    thickness = 1  # Thickness for extruded meshes

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
            min_polygon_area=1e-3,
            simplify_tolerance=0.5,
            max_segments=10000,
            min_area_fraction=0.0001,
        ),
        mesh_combination=MeshCombinationConfig(
            merge_threshold=1e-6,
        ),
        triangulation=TriangulationConfig(
            triangulator_add_interior_points=True,
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
            simplification_method="none",
            target_triangle_count=100000,
            voxel_size=0.05,
        ),
        stateless=not create_visuals,
    )

    heightmap_data, generator = generate_mesh(
        filepath=heightmap_path,
        config=config,
        save_path=save_mesh_path,
    )

    if create_visuals:
        save_path = data_dir / "debug_outs" / "hawaii_contours.png"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        contour_plot(generator=generator, save_path=save_path)
