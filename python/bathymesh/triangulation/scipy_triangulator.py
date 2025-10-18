"""Scipy-based triangulator using Delaunay triangulation."""

from typing import Tuple, List, Optional, Union
import numpy as np
from scipy.spatial import Delaunay
from shapely.geometry import Polygon, MultiPolygon, Point
import logging
from .base_triangulator import BaseTriangulator

logger = logging.getLogger(__name__)


class ScipyTriangulator(BaseTriangulator):
    """
    Handles polygon triangulation using scipy.spatial.Delaunay.
    
    Note: This implementation generates unconstrained Delaunay triangulation
    and then filters triangles to keep only those inside the polygon.
    It does not preserve polygon boundary segments like constrained triangulators.
    """
    
    add_interior_points: bool
    interior_point_density: float
    
    def __init__(
        self, 
        add_interior_points: bool = True, 
        interior_point_density: float = 1.0
    ):
        """
        Initialize scipy triangulator.
        
        Args:
            add_interior_points: If True, adds interior points for better triangulation
            interior_point_density: Density factor for interior point generation
        """
        self.add_interior_points = add_interior_points
        self.interior_point_density = interior_point_density
    
    def triangulate_polygon(
        self, 
        geometries: Union[Polygon, MultiPolygon, List[Polygon]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Triangulate polygon geometries using scipy Delaunay triangulation.
        
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
        Triangulate a single Shapely polygon using scipy Delaunay.
        
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
        
        # Extract boundary points
        boundary_points = self._extract_boundary_points(polygon)
        
        # Optionally add interior points for better triangulation
        if self.add_interior_points:
            interior_points = self._generate_interior_points(polygon)
            all_points = np.vstack([boundary_points, interior_points])
        else:
            all_points = boundary_points
        
        # Perform Delaunay triangulation
        logger.info(f"Triangulating polygon with {len(all_points)} points "
                   f"({len(boundary_points)} boundary, "
                   f"{len(all_points) - len(boundary_points)} interior)")
        
        try:
            delaunay = Delaunay(all_points)
            
            # Filter triangles to keep only those inside the polygon
            valid_triangles = self._filter_interior_triangles(
                all_points, delaunay.simplices, polygon
            )
            
            return all_points, valid_triangles
            
        except Exception as e:
            raise ValueError(f"Delaunay triangulation failed: {e}") from e
    
    def _extract_boundary_points(self, polygon: Polygon) -> np.ndarray:
        """
        Extract boundary points from polygon (exterior + holes).
        
        Args:
            polygon: Shapely Polygon object
            
        Returns:
            Array of boundary points (N, 2)
        """
        points = []
        
        # Add exterior ring points (excluding duplicate last point)
        exterior_coords = np.array(polygon.exterior.coords[:-1])
        points.append(exterior_coords)
        
        # Add hole points
        for interior in polygon.interiors:
            hole_coords = np.array(interior.coords[:-1])
            points.append(hole_coords)
        
        return np.vstack(points) if points else np.empty((0, 2))
    
    def _generate_interior_points(self, polygon: Polygon) -> np.ndarray:
        """
        Generate interior points for better triangulation quality.
        
        Args:
            polygon: Shapely Polygon object
            
        Returns:
            Array of interior points (N, 2)
        """
        # Get polygon bounds
        minx, miny, maxx, maxy = polygon.bounds
        width = maxx - minx
        height = maxy - miny
        area = polygon.area
        
        # Estimate number of interior points based on area and density
        # Use a simple grid-based approach
        target_area_per_point = area / (self.interior_point_density * 100)
        grid_spacing = np.sqrt(target_area_per_point)
        
        # Generate grid points
        x_points = np.arange(minx + grid_spacing/2, maxx, grid_spacing)
        y_points = np.arange(miny + grid_spacing/2, maxy, grid_spacing)
        
        interior_points = []
        for x in x_points:
            for y in y_points:
                point = Point(x, y)
                if polygon.contains(point):
                    interior_points.append([x, y])
        
        if not interior_points:
            logger.warning("No interior points generated - triangulation may be poor quality")
            return np.empty((0, 2))
        
        logger.debug(f"Generated {len(interior_points)} interior points")
        return np.array(interior_points)
    
    def _filter_interior_triangles(
        self, 
        points: np.ndarray, 
        triangles: np.ndarray, 
        polygon: Polygon
    ) -> np.ndarray:
        """
        Filter triangles to keep only those inside the polygon.
        
        Args:
            points: All triangulation points (N, 2)
            triangles: All triangles from Delaunay (M, 3)
            polygon: Original polygon for containment testing
            
        Returns:
            Filtered triangles that are inside the polygon
        """
        valid_triangles = []
        
        for triangle in triangles:
            # Get triangle vertices
            tri_points = points[triangle]
            
            # Check if triangle centroid is inside polygon
            centroid_x = np.mean(tri_points[:, 0])
            centroid_y = np.mean(tri_points[:, 1])
            centroid = Point(centroid_x, centroid_y)
            
            if polygon.contains(centroid):
                valid_triangles.append(triangle)
        
        if not valid_triangles:
            raise ValueError("No valid triangles found inside polygon")
        
        logger.debug(f"Filtered {len(triangles)} triangles to {len(valid_triangles)} "
                    f"interior triangles")
        
        return np.array(valid_triangles)
