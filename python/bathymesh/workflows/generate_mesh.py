
from pathlib import Path
from typing import Union

import open3d as o3d

from bathymesh.data_model import HeightmapData, MeshData
from bathymesh.config import MeshConfig, SimplificationMethod
from bathymesh.data_model import HeightmapData, MeshData
from bathymesh.mesh_generator import MeshGenerator


def generate_mesh(
    heightmap_data: HeightmapData,
    config: MeshConfig,
    save_path: Union[str, Path, None] = None,
    stateless: bool = True,
) -> tuple[
    MeshData,
    MeshGenerator,
]:
    """
    Generate a multi-level 3D mesh from heightmap data.

    Args:
        heightmap_data: Input heightmap data with coordinates
        config: Mesh generation configuration
        save_path: Optional path to save the mesh as STL file
        stateless: Whether to run in stateless mode (no debug snapshots)

    Returns:
        MeshData containing the generated 3D mesh
    """
    generator = MeshGenerator(config=config, stateless=stateless)

    mesh_data = generator.execute(heightmap_data)

    if save_path is not None:
        o3d.io.write_triangle_mesh(str(save_path), mesh_data.data)

    return mesh_data, generator
