"""Mesh export utilities for bathymesh."""

from typing import Union
from pathlib import Path
import open3d as o3d
import logging

from ..data_structures import MeshInfo, MeshFormat

logger = logging.getLogger(__name__)

def export_mesh(
    mesh: o3d.geometry.TriangleMesh, 
    filepath: Union[str, Path],
    format_override: Union[str, None] = None
) -> bool:
    """
    Export mesh to file.
    
    Args:
        mesh: Open3D TriangleMesh to export
        filepath: Output file path
        format_override: Override format detection (e.g., 'stl', 'ply')
        
    Returns:
        True if export successful, False otherwise
        
    Raises:
        ValueError: If mesh is empty or format unsupported
    """
    if len(mesh.vertices) == 0:
        raise ValueError("Cannot export empty mesh")
    
    filepath = Path(filepath)
    
    # Determine format
    try:
        if format_override:
            mesh_format = MeshFormat.from_extension(format_override)
        else:
            mesh_format = MeshFormat.from_extension(filepath.suffix)
    except ValueError as e:
        raise ValueError(str(e)) from e
    
    # Ensure output directory exists
    filepath.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        success = o3d.io.write_triangle_mesh(str(filepath), mesh)
        if success:
            logger.info(f"Successfully exported mesh to {filepath}")
        else:
            logger.error(f"Failed to export mesh to {filepath}")
        return success
    except Exception as e:
        logger.error(f"Exception during mesh export: {e}")
        return False


def export_stl(
    mesh: o3d.geometry.TriangleMesh, 
    filepath: Union[str, Path]
) -> bool:
    """
    Export mesh to STL format (convenience function).
    
    Args:
        mesh: Open3D TriangleMesh to export
        filepath: Output STL file path
        
    Returns:
        True if export successful, False otherwise
    """
    return export_mesh(mesh, filepath, format_override='stl')


def get_mesh_info(mesh: o3d.geometry.TriangleMesh) -> MeshInfo:
    """
    Get information about a mesh.
    
    Args:
        mesh: Open3D TriangleMesh to analyze
        
    Returns:
        MeshInfo dataclass with mesh statistics
    """
    mesh_info = MeshInfo(
        num_vertices=len(mesh.vertices),
        num_triangles=len(mesh.triangles),
        has_vertex_normals=mesh.has_vertex_normals(),
        has_triangle_normals=mesh.has_triangle_normals(),
        is_watertight=mesh.is_watertight(),
        is_orientable=mesh.is_orientable(),
    )
    
    if len(mesh.vertices) > 0:
        bbox = mesh.get_axis_aligned_bounding_box()
        mesh_info.bounding_box_min = bbox.min_bound.tolist()
        mesh_info.bounding_box_max = bbox.max_bound.tolist()
        mesh_info.bounding_box_extent = bbox.get_extent().tolist()
    
    return mesh_info
