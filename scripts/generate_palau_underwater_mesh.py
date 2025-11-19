import logging
from pathlib import Path

import geopandas as gpd
import numpy as np
from bathy.data_model import HeightmapData, MeshUnits
from bathy.mesh_post_processor import SimplificationMethod
from bathy.workflows.generate_mesh import generate_mesh
from matplotlib import pyplot as plt

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    data_dir = Path(__file__).parent.parent / "data"

    heightmap_path = data_dir / "processed" / "palau_heightmap_bathy.npy"
    save_mesh_path = data_dir / "meshes" / "palau_underwater_mesh.stl"

    save_mesh_path.parent.mkdir(parents=True, exist_ok=True)

    raw_heightmap_data = np.load(heightmap_path)

    exterior_buffer_width = 20
    exterior_buffer_value = 0.0
    offset = 110.0

    thresholds = [x for x in np.linspace(0, 209, 30)]  # Height thresholds
    # thresholds = [x for x in np.linspace(0, 199, 3)]  # Height thresholds

    layer_spacing = 0.5  # Vertical spacing between levels

    # Mesh parameters
    units = MeshUnits(
        units_x=0.2,  # X-axis scaling factor
        units_y=0.2,  # Y-axis scaling factor
        units_z=1.6,  # Z-axis (height) scaling factor
    )

    base_height = 0.0  # Base height for mesh
    thickness = 0.5  # Thickness for extruded meshes

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
        thresholds=thresholds,
        save_path=save_mesh_path,
        base_height=base_height,
        layer_thickness=thickness,
        post_process_mesh=True,
        # Contour extraction
        contour_extraction_min_polygon_area=1e-2,
        contour_extraction_simplify_tolerance=0.5,
        contour_extraction_max_segments=3000,
        contour_extraction_min_area_fraction=0.1,
        # Combiner
        combiner_merge_threshold=1e-6,
        # Triangulator
        triangulator_add_interior_points=True,
        triangulator_interior_point_density=1.0,
        # Post-processing: Basic cleanup
        post_p_remove_degenerate_triangles=True,
        post_p_remove_duplicated_vertices=True,
        post_p_remove_duplicated_triangles=True,
        post_p_remove_unreferenced_vertices=True,
        # Post-processing: Vertex merging
        post_p_merge_close_vertices=True,
        post_p_merge_vertices_threshold=1e-6,
        # Post-processing: Simplification
        post_p_simplification_method=SimplificationMethod.NONE,
        post_p_target_triangle_count=100000,
        post_p_voxel_size=0.05,
        stateless=not create_visuals,
    )

    if create_visuals:
        # Plot Contours
        fig, ax = plt.subplots(figsize=(10, 10))

        max_idx = max(generator.threshold_snapshots.keys())
        for idx, snap in generator.threshold_snapshots.items():
            contours = snap.contours
            gdf = gpd.GeoDataFrame(geometry=contours)
            gdf["level"] = idx
            gdf.plot(
                ax=ax,
                alpha=0.5,
                edgecolor="black",
                label=f"Threshold {idx}",
                cmap="viridis",
                vmin=0,
                vmax=max_idx,
                legend=True,
            )

        ax.set_title("Extracted Contours at Different Height Thresholds")

        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")
        ax.legend(title="Height Thresholds")
        plt.grid(True)

        save_path = data_dir / "debug_outs" / "palau_contours.png"
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path)
