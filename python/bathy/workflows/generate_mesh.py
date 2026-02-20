"""Mesh generation workflow with optional splitting support."""

import logging
from pathlib import Path
from typing import Union

import numpy as np
import open3d as o3d

from bathy.config import MeshGenerationConfig
from bathy.data_model import HeightmapData, SplitMeshResult
from bathy.mesh_generator import MeshGenerator

logger = logging.getLogger(__name__)


def generate_mesh(
    filepath: Path,
    config: MeshGenerationConfig,
    save_path: Union[Path, None] = None,
) -> tuple[Union[None,SplitMeshResult], MeshGenerator]:
    """
    Generate a multi-level 3D mesh from heightmap data.

    Args:
        filepath: Path to the heightmap numpy file (.npy)
        config: Mesh generation configuration
        save_path: Optional path to save the mesh as STL file.
            If splitting is enabled, split pieces are saved with numbered suffixes.

    Returns:
        Tuple of (SplitMeshResult, MeshGenerator)
            - SplitMeshResult contains combined_mesh and optional split_meshes
            - MeshGenerator for accessing threshold snapshots if needed
    """
    raw_heightmap_data = np.load(filepath)

    heightmap_data = HeightmapData(data=raw_heightmap_data)

    heightmap_data.post_process(config=config)

    generator = MeshGenerator(config=config)

    result = generator.execute(heightmap_data)

    if save_path is not None:
        if result is not None:
            save_mesh_result(result, save_path)

    return result, generator


def save_mesh_result(
    result: SplitMeshResult,
    save_path: Path,
    save_combined: bool = True,
) -> list[Path]:
    """
    Save mesh result to disk.

    Handles three output scenarios:
    1. Single mesh (no splitting): saves to save_path
    2. Tile-based splitting: saves each tile as mesh_r{row}c{col}.stl
    3. Plane-based splitting (deprecated): saves as mesh_part01.stl, etc.

    Args:
        result: The SplitMeshResult from mesh generation
        save_path: Base path for saving (e.g., 'output/mesh.stl')
        save_combined: Whether to save the combined mesh (default: True)

    Returns:
        List of paths to saved mesh files
    """
    saved_paths: list[Path] = []
    save_path = Path(save_path)

    # Ensure parent directory exists
    save_path.parent.mkdir(parents=True, exist_ok=True)

    # Save combined mesh
    if save_combined:
        combined_path = save_path
        if result.has_splits or result.has_tiles:
            # Use _combined suffix when there are also split pieces or tiles
            combined_path = save_path.with_stem(f"{save_path.stem}_combined")

        _write_mesh(result.combined_mesh, combined_path)
        saved_paths.append(combined_path)
        logger.info(f"Saved combined mesh to {combined_path}")

    # Save tile meshes if present (heightmap-based splitting)
    if result.has_tiles:
        for i, (mesh, tile_id) in enumerate(zip(result.split_meshes, result.tile_ids)):
            tile_path = save_path.with_stem(f"{save_path.stem}_{tile_id}")
            _write_mesh(mesh, tile_path)
            saved_paths.append(tile_path)
            logger.info(
                f"Saved tile {tile_id} ({i + 1}/{len(result.tile_ids)}) to {tile_path}"
            )
    # Save split pieces if present (plane-based splitting, deprecated)
    elif result.has_splits:
        for i, mesh in enumerate(result.split_meshes):
            piece_path = save_path.with_stem(f"{save_path.stem}_part{i + 1:02d}")
            _write_mesh(mesh, piece_path)
            saved_paths.append(piece_path)
            logger.info(
                f"Saved split piece {i + 1}/{result.num_pieces} to {piece_path}"
            )

    return saved_paths


def _write_mesh(mesh: o3d.geometry.TriangleMesh, path: Path) -> None:
    """
    Write a mesh to disk.

    Args:
        mesh: Open3D TriangleMesh to save
        path: Output path (format determined by extension)

    Raises:
        IOError: If mesh writing fails
    """
    success = o3d.io.write_triangle_mesh(str(path), mesh)
    if not success:
        raise IOError(f"Failed to write mesh to {path}")
