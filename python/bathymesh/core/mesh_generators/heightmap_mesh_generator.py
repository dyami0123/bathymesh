"""Heightmap mesh generation implementation."""

from typing import Union, List, Callable, Optional, TYPE_CHECKING
import numpy as np
import open3d as o3d
from shapely.geometry import Polygon, MultiPolygon
import logging

from .base_mesh_generator import BaseMeshGenerator

if TYPE_CHECKING:
    from ..heightmap_handler import HeightmapHandler

logger = logging.getLogger(__name__)


class HeightmapMeshGenerator(BaseMeshGenerator):
    """Generates meshes with height variations based on heightmap data."""
    
    def generate_mesh(
        self, 
        heightmap_handler: 'HeightmapHandler',
        base_height: float = 0.0,
        use_contours: bool = False,
        threshold: Optional[float] = None,
        use_surface_mesh: bool = False
    ) -> o3d.geometry.TriangleMesh:
        """
        Generate a mesh with height variations from heightmap data.
        
        Args:
            heightmap_handler: HeightmapHandler containing heightmap data
            base_height: Base Z-coordinate to add to height function results
            use_contours: If True, extract contours at threshold, else use bounding polygon
            threshold: Height threshold for contour extraction (required if use_contours=True)
            use_surface_mesh: If True, create a surface mesh, else use triangulated polygon with heights
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If parameters are invalid or mesh generation fails
        """
        if use_surface_mesh:
            return self._create_surface_mesh(heightmap_handler, base_height)
        
        # Use polygon-based approach with height function
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
        
        height_function = heightmap_handler.get_height_function()
        return self._create_heightmap_mesh_single(polygon, height_function, base_height)
    
    def generate_mesh_from_function(
        self,
        geometries: Union[Polygon, MultiPolygon, List[Polygon]],
        height_function: Callable[[float, float], float],
        base_height: float = 0.0
    ) -> o3d.geometry.TriangleMesh:
        """
        Generate a mesh using a custom height function (legacy interface).
        
        Args:
            geometries: Single polygon, MultiPolygon, or list of polygons
            height_function: Function that takes (x, y) coordinates and returns height
            base_height: Base Z-coordinate to add to height function results
            
        Returns:
            Open3D TriangleMesh object
        """
        polygons = self._normalize_geometries(geometries)
        
        # For now, handle single polygon - future enhancement for multiple polygons
        if len(polygons) != 1:
            raise ValueError("Multiple polygon mesh generation not yet implemented")
            
        polygon = polygons[0]
        return self._create_heightmap_mesh_single(polygon, height_function, base_height)
    
    def _create_surface_mesh(
        self, 
        heightmap_handler: 'HeightmapHandler',
        base_height: float
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a surface mesh directly from heightmap data.
        
        Args:
            heightmap_handler: HeightmapHandler containing heightmap data
            base_height: Base Z-coordinate to add to heights
            
        Returns:
            Open3D TriangleMesh object
        """
        vertices, faces = heightmap_handler.create_surface_mesh_data()
        
        # Add base height to all vertices
        if base_height != 0.0:
            vertices[:, 2] += base_height
        
        mesh = self._create_mesh_from_vertices_faces(vertices, faces)
        
        logger.debug(f"Created surface mesh with {len(vertices)} vertices and {len(faces)} triangles")
        return mesh
    
    def _create_heightmap_mesh_single(
        self, 
        polygon: Polygon, 
        height_function: Callable[[float, float], float],
        base_height: float
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a heightmap mesh from a single polygon.
        
        Args:
            polygon: Shapely Polygon to convert
            height_function: Function that takes (x, y) coordinates and returns height
            base_height: Base Z-coordinate to add to height function results
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If polygon triangulation fails
        """
        try:
            vertices_2d, triangles = self.triangulator.triangulate_polygon(polygon)
        except Exception as e:
            raise ValueError(f"Failed to triangulate polygon: {e}") from e
        
        # Apply height function to each vertex
        heights = np.array([
            base_height + height_function(x, y) 
            for x, y in vertices_2d
        ])
        
        # Create 3D vertices with computed heights
        vertices_3d = np.column_stack((vertices_2d, heights))
        
        mesh = self._create_mesh_from_vertices_faces(vertices_3d, triangles)
        
        logger.debug(f"Created heightmap mesh with {len(vertices_3d)} vertices and {len(triangles)} triangles")
        return mesh
    
    def generate_mesh_from_array(
        self,
        geometries: Union[Polygon, MultiPolygon, List[Polygon]],
        height_array: np.ndarray,
        x_coords: np.ndarray,
        y_coords: np.ndarray,
        base_height: float = 0.0
    ) -> o3d.geometry.TriangleMesh:
        """
        Generate a mesh using a 2D height array for interpolation.
        
        Args:
            geometries: Single polygon, MultiPolygon, or list of polygons
            height_array: 2D array of height values
            x_coords: 1D array of x-coordinates corresponding to height_array columns
            y_coords: 1D array of y-coordinates corresponding to height_array rows
            base_height: Base Z-coordinate to add to interpolated heights
            
        Returns:
            Open3D TriangleMesh object
        """
        from scipy.interpolate import RegularGridInterpolator
        
        # Create interpolator
        interpolator = RegularGridInterpolator(
            (y_coords, x_coords), 
            height_array, 
            method='linear',
            bounds_error=False,
            fill_value=0.0
        )
        
        # Create height function using interpolator
        def height_function(x: float, y: float) -> float:
            try:
                return float(interpolator((y, x)))
            except (ValueError, IndexError):
                return 0.0
        
        return self.generate_mesh(geometries, height_function, base_height)
