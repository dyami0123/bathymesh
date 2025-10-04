"""Abstract base class for mesh generation implementations."""

from abc import ABC, abstractmethod
from typing import Union, List, Optional, TYPE_CHECKING
import numpy as np
import open3d as o3d
from shapely.geometry import Polygon, MultiPolygon

from ...triangulation import BaseTriangulator

if TYPE_CHECKING:
    from ..heightmap_processor import HeightmapProcessor
    from ..mesh_combiner import MeshCombiner
    from ..heightmap_handler import HeightmapHandler


class BaseMeshGenerator(ABC):
    """Abstract base class for mesh generation implementations."""
    
    triangulator: BaseTriangulator
    heightmap_processor: Optional['HeightmapProcessor']
    mesh_combiner: Optional['MeshCombiner']
    
    def __init__(
        self, 
        triangulator: BaseTriangulator,
        heightmap_processor: Optional['HeightmapProcessor'] = None,
        mesh_combiner: Optional['MeshCombiner'] = None
    ):
        """
        Initialize mesh generator.
        
        Args:
            triangulator: Triangulation engine to use
            heightmap_processor: Optional heightmap processor for contour extraction
            mesh_combiner: Optional mesh combiner for mesh operations
        """
        self.triangulator = triangulator
        self.heightmap_processor = heightmap_processor
        self.mesh_combiner = mesh_combiner
    
    @abstractmethod
    def generate_mesh(
        self, 
        heightmap_handler: 'HeightmapHandler',
        **kwargs
    ) -> o3d.geometry.TriangleMesh:
        """
        Generate a mesh from heightmap data.
        
        Args:
            heightmap_handler: HeightmapHandler containing heightmap data and utilities
            **kwargs: Generator-specific parameters
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If heightmap data is invalid or mesh generation fails
        """
        pass
    
    def _normalize_geometries(
        self, 
        geometries: Union[Polygon, MultiPolygon, List[Polygon]]
    ) -> List[Polygon]:
        """
        Normalize input geometries to a list of polygons.
        
        Delegates to the triangulator's normalization method to avoid code duplication.
        
        Args:
            geometries: Input geometries in various formats
            
        Returns:
            List of Polygon objects
            
        Raises:
            ValueError: If input contains invalid geometries
        """
        return self.triangulator._normalize_geometries(geometries)
    
    def _create_mesh_from_vertices_faces(
        self, 
        vertices: np.ndarray, 
        faces: np.ndarray
    ) -> o3d.geometry.TriangleMesh:
        """
        Create Open3D mesh from vertices and faces.
        
        Args:
            vertices: (N, 3) array of 3D vertex coordinates
            faces: (M, 3) array of triangle vertex indices
            
        Returns:
            Open3D TriangleMesh object
        """
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(faces)
        mesh.compute_vertex_normals()
        return mesh
