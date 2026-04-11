from pathlib import Path
from typing import Union

import numpy as np
import open3d as o3d
from bathy.python.bathy.config import MeshGenerationConfig
from bathy.python.bathy.data_model import HeightmapData, MeshData
from bathy.python.bathy.mesh_generator import MeshGenerator


def generate_mesh(
    filepath: Path,
    config: MeshGenerationConfig,
    save_path: Union[Path, None] = None,
) -> tuple[
    MeshData,
    MeshGenerator,
]:
    """
    Generate a multi-level 3D mesh from heightmap data.

    Args:
        heightmap_data: Input heightmap data with coordinates
        save_path: Optional path to save the mesh as STL file

    Returns:
        MeshData containing the generated 3D mesh
    """

    raw_heightmap_data = np.load(filepath)

    heightmap_data = HeightmapData(data=raw_heightmap_data)

    heightmap_data.post_process(config=config)

    generator = MeshGenerator(config=config)

    mesh_data = generator.execute(heightmap_data)

    if save_path is not None:
        o3d.io.write_triangle_mesh(str(save_path), mesh_data.data)

    return mesh_data, generator
