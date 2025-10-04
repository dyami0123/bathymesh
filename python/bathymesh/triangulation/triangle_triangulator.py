"""Wrapper for the triangle library to provide clean triangulation interface."""

from typing import Tuple, List, Optional, Union
import numpy as np
import triangle as tr
from shapely.geometry import Polygon, MultiPolygon

from .base_triangulator import BaseTriangulator


class TriangleTriangulator(BaseTriangulator):
    """Handles polygon triangulation using the triangle library."""
    
    quality_mesh: bool
    
    def __init__(self, quality_mesh: bool = True):
        """
        Initialize triangulator.
        
        Args:
            quality_mesh: If True, generates quality triangles (Delaunay)
        """
        self.quality_mesh = quality_mesh
    
    def triangulate_polygon(
        self, 
        geometries: Union[Polygon, MultiPolygon, List[Polygon]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Triangulate polygon geometries using the triangle library.
        
        Args:
            geometries: Single polygon, MultiPolygon, or list of polygons to triangulate
            
        Returns:
            Tuple of (vertices, triangles) where:
            - vertices: (N, 2) array of 2D vertex coordinates
            - triangles: (M, 3) array of triangle vertex indices
            
        Raises:
            ValueError: If geometries are invalid or triangulation fails
        """
        polygons = self._normalize_geometries(geometries)
        
        # For now, handle single polygon - future enhancement for multiple polygons
        if len(polygons) != 1:
            raise ValueError("Multiple polygon triangulation not yet implemented")
            
        polygon = polygons[0]
        return self._triangulate_single_polygon(polygon)
    
    def _triangulate_single_polygon(self, polygon: Polygon) -> Tuple[np.ndarray, np.ndarray]:
        """
        Triangulate a single Shapely polygon using the triangle library.
        
        Args:
            polygon: Shapely Polygon object to triangulate
            
        Returns:
            Tuple of (vertices, triangles) where:
            - vertices: (N, 2) array of 2D vertex coordinates
            - triangles: (M, 3) array of triangle vertex indices
            
        Raises:
            ValueError: If polygon is invalid or triangulation fails
        """
        if not polygon.is_valid:
            raise ValueError("Input polygon is not valid")
            
        # Extract exterior and holes
        exterior = np.array(polygon.exterior.coords[:-1])  # Remove duplicate last point
        holes = [np.array(ring.coords[:-1]) for ring in polygon.interiors]
        
        # Build triangle input data structure
        vertices, segments, hole_points = self._build_triangle_input(exterior, holes)
        
        data = {
            'vertices': vertices,
            'segments': segments,
        }
        if hole_points:
            data['holes'] = np.array(hole_points)
        
        # Triangulate with appropriate flags
        flags = 'p'  # Use PSLG (Planar Straight Line Graph)
        if self.quality_mesh:
            flags += 'q'  # Add quality mesh generation
            
        try:
            result = tr.triangulate(data, flags)
            return result['vertices'], result['triangles']
        except Exception as e:
            raise ValueError(f"Triangulation failed: {e}") from e
    
    def _build_triangle_input(
        self, 
        exterior: np.ndarray, 
        holes: List[np.ndarray]
    ) -> Tuple[np.ndarray, np.ndarray, List[Tuple[float, float]]]:
        """
        Build vertices, segments, and hole points for triangle library.
        
        Args:
            exterior: Exterior ring vertices
            holes: List of hole ring vertices
            
        Returns:
            Tuple of (vertices, segments, hole_points)
        """
        vertices = []
        segments = []
        hole_points = []
        vertex_idx = 0
        
        # Add exterior ring
        for i, vertex in enumerate(exterior):
            vertices.append((vertex[0], vertex[1]))
            segments.append((vertex_idx + i, vertex_idx + ((i + 1) % len(exterior))))
        vertex_idx += len(exterior)
        
        # Add holes
        for hole in holes:
            # Calculate hole marker point (interior point)
            hole_polygon = Polygon(hole)
            if hole_polygon.is_valid:
                centroid = hole_polygon.centroid.coords[0]
                hole_points.append(centroid)
            
            # Add hole vertices and segments
            for i, vertex in enumerate(hole):
                vertices.append((vertex[0], vertex[1]))
                segments.append((vertex_idx + i, vertex_idx + ((i + 1) % len(hole))))
            vertex_idx += len(hole)
        
        return np.array(vertices), np.array(segments), hole_points
