from pathlib import Path
from typing import Union

import open3d as o3d

from bathy.data_model import HeightmapData, MeshData
from bathy.mesh_generator import MeshGenerator
from bathy.mesh_post_processor import SimplificationMethod


def generate_mesh(
    heightmap_data: HeightmapData,
    thresholds: list[float],
    save_path: Union[str, Path, None] = None,
    base_height: float = 0.0,
    layer_thickness: float = 1.0,
    post_process_mesh: bool = True,
    # Contour extraction
    contour_extraction_min_polygon_area: float = 1e-2,
    contour_extraction_simplify_tolerance: float = 0.5,
    contour_extraction_max_segments: int = 100,
    contour_extraction_min_area_fraction: float = 0.01,
    # Combiner
    combiner_merge_threshold: float = 1e-6,
    # Triangulator
    triangulator_add_interior_points: bool = True,
    triangulator_interior_point_density: float = 1.0,
    # Post-processing: Basic cleanup
    post_p_remove_degenerate_triangles: bool = True,
    post_p_remove_duplicated_vertices: bool = True,
    post_p_remove_duplicated_triangles: bool = True,
    post_p_remove_unreferenced_vertices: bool = True,
    # Post-processing: Vertex merging
    post_p_merge_close_vertices: bool = False,
    post_p_merge_vertices_threshold: float = 1e-6,
    # Post-processing: Simplification
    post_p_simplification_method: SimplificationMethod = SimplificationMethod.NONE,
    post_p_target_triangle_count: int = 100000,
    post_p_voxel_size: float = 0.05,
    stateless: bool = True,
) -> tuple[
    MeshData,
    MeshGenerator,
]:
    """
    Generate a multi-level 3D mesh from heightmap data.

    Args:
        heightmap_data: Input heightmap data with coordinates
        thresholds: List of height thresholds for each level
        save_path: Optional path to save the mesh as STL file
        base_height: Z-coordinate of the base level
        layer_thickness: Thickness of each extruded layer
        post_process_mesh: Whether to apply post-processing to meshes
        contour_extraction_min_polygon_area: Minimum polygon area for contour extraction
        combiner_merge_threshold: Threshold for merging close vertices when combining meshes
        triangulator_add_interior_points: Whether to add interior points during triangulation
        triangulator_interior_point_density: Density of interior points (points per unit area)
        post_p_remove_degenerate_triangles: Remove degenerate triangles
        post_p_remove_duplicated_vertices: Remove duplicated vertices
        post_p_remove_duplicated_triangles: Remove duplicated triangles
        post_p_remove_unreferenced_vertices: Remove unreferenced vertices
        post_p_merge_close_vertices: Merge vertices that are very close
        post_p_merge_vertices_threshold: Distance threshold for merging vertices
        post_p_simplification_method: Method for mesh simplification
        post_p_target_triangle_count: Target triangle count for quadric decimation
        post_p_voxel_size: Voxel size for vertex clustering simplification

    Returns:
        MeshData containing the generated 3D mesh
    """
    generator = MeshGenerator(
        thresholds=thresholds,
        base_height=base_height,
        layer_thickness=layer_thickness,
        post_process_mesh=post_process_mesh,
        contour_extraction_min_polygon_area=contour_extraction_min_polygon_area,
        contour_extraction_simplify_tolerance=contour_extraction_simplify_tolerance,
        contour_extraction_max_segments=contour_extraction_max_segments,
        contour_extraction_min_area_fraction=contour_extraction_min_area_fraction,
        combiner_merge_threshold=combiner_merge_threshold,
        triangulator_add_interior_points=triangulator_add_interior_points,
        triangulator_interior_point_density=triangulator_interior_point_density,
        post_p_remove_degenerate_triangles=post_p_remove_degenerate_triangles,
        post_p_remove_duplicated_vertices=post_p_remove_duplicated_vertices,
        post_p_remove_duplicated_triangles=post_p_remove_duplicated_triangles,
        post_p_remove_unreferenced_vertices=post_p_remove_unreferenced_vertices,
        post_p_merge_close_vertices=post_p_merge_close_vertices,
        post_p_merge_vertices_threshold=post_p_merge_vertices_threshold,
        post_p_simplification_method=post_p_simplification_method,
        post_p_target_triangle_count=post_p_target_triangle_count,
        post_p_voxel_size=post_p_voxel_size,
        stateless=stateless,
    )

    mesh_data = generator.execute(heightmap_data)

    if save_path is not None:
        o3d.io.write_triangle_mesh(str(save_path), mesh_data.data)

    return mesh_data, generator
