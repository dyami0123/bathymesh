"""Bathymesh: A Python library for converting maps and heightmaps to 3D printable meshes."""

from .core import HeightmapProcessor, PolygonMeshGenerator, MeshCombiner
from .triangulation import TriangleTriangulator
from .io import export_mesh, export_stl, get_mesh_info
from .utils import validate_heightmap, normalize_heightmap, calculate_polygon_stats, create_test_heightmap
from .workflow import BathymeshWorkflow
from .data_structures import PolygonStats, MeshInfo, MeshScaling, ContourMeshParams, MeshFormat

__version__ = "0.1.0"

__all__ = [
    "BathymeshWorkflow",
    "HeightmapProcessor",
    "PolygonMeshGenerator", 
    "MeshCombiner",
    "TriangleTriangulator",
    "export_mesh",
    "export_stl", 
    "get_mesh_info",
    "validate_heightmap",
    "normalize_heightmap",
    "calculate_polygon_stats",
    "create_test_heightmap",
    "PolygonStats",
    "MeshInfo",
    "MeshScaling",
    "ContourMeshParams", 
    "MeshFormat",
]