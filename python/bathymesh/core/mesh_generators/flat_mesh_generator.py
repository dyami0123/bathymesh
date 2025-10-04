"""Flat mesh generation implementation."""

from typing import Union, List, Optional, TYPE_CHECKING
import numpy as np
import open3d as o3d
from shapely.geometry import Polygon, MultiPolygon
import logging

from .base_mesh_generator import BaseMeshGenerator

if TYPE_CHECKING:
    from ..heightmap_handler import HeightmapHandler

logger = logging.getLogger(__name__)


class FlatMeshGenerator(BaseMeshGenerator):
    """Generates flat meshes from heightmap data at a specified height."""
    
    def generate_mesh(
        self, 
        heightmap_handler: 'HeightmapHandler',
        height: float = 0.0,
        use_contours: bool = False,
        threshold: Optional[float] = None
    ) -> o3d.geometry.TriangleMesh:
        """
        Generate a flat mesh from heightmap data at specified height.
        
        Args:
            heightmap_handler: HeightmapHandler containing heightmap data
            height: Z-coordinate for the flat mesh
            use_contours: If True, extract contours at threshold, else use bounding polygon
            threshold: Height threshold for contour extraction (required if use_contours=True)
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If parameters are invalid or mesh generation fails
        """
        if use_contours:
            if threshold is None:
                raise ValueError("threshold must be provided when use_contours=True")
            polygons = heightmap_handler.extract_contour_polygons(threshold)
            if not polygons:
                logger.warning("No contours found at threshold, using bounding polygon")
                polygon = heightmap_handler.get_bounding_polygon()
            else:
                # For now, use the first/largest polygon
                polygon = max(polygons, key=lambda p: p.area)
        else:
            polygon = heightmap_handler.get_bounding_polygon()
        
        return self._create_flat_mesh_single(polygon, height)
    
    def generate_mesh_from_polygons(
        self,
        geometries: Union[Polygon, MultiPolygon, List[Polygon]],
        height: float = 0.0
    ) -> o3d.geometry.TriangleMesh:
        """
        Generate a flat mesh from explicit polygon geometries (legacy interface).
        
        Args:
            geometries: Single polygon, MultiPolygon, or list of polygons
            height: Z-coordinate for the flat mesh
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If polygon triangulation fails
        """
        polygons = self._normalize_geometries(geometries)
        
        # For now, handle single polygon - future enhancement for multiple polygons
        if len(polygons) != 1:
            raise ValueError("Multiple polygon mesh generation not yet implemented")
            
        polygon = polygons[0]
        return self._create_flat_mesh_single(polygon, height)
    
    def _create_flat_mesh_single(
        self, 
        polygon: Polygon, 
        height: float
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a flat mesh from a single polygon at specified height.
        
        Args:
            polygon: Shapely Polygon to convert
            height: Z-coordinate for the flat mesh
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If polygon triangulation fails
        """
        try:
            vertices_2d, triangles = self.triangulator.triangulate_polygon(polygon)
        except Exception as e:
            raise ValueError(f"Failed to triangulate polygon: {e}") from e
        
        # Create 3D vertices at specified height
        vertices_3d = np.column_stack((vertices_2d, np.full(len(vertices_2d), height)))
        
        mesh = self._create_mesh_from_vertices_faces(vertices_3d, triangles)
        
        logger.debug(f"Created flat mesh with {len(vertices_3d)} vertices and {len(triangles)} triangles")
        return mesh
