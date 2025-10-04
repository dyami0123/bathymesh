"""Abstract base class for triangulation implementations."""

from abc import ABC, abstractmethod
from typing import Tuple, Union, List
import numpy as np
from shapely.geometry import Polygon, MultiPolygon


class BaseTriangulator(ABC):
    """Abstract base class for polygon triangulation implementations."""
    
    @abstractmethod
    def triangulate_polygon(
        self, 
        geometries: Union[Polygon, MultiPolygon, List[Polygon]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Triangulate polygon geometries.
        
        Args:
            geometries: Single polygon, MultiPolygon, or list of polygons to triangulate
            
        Returns:
            Tuple of (vertices, triangles) where:
            - vertices: (N, 2) array of 2D vertex coordinates
            - triangles: (M, 3) array of triangle vertex indices
            
        Raises:
            ValueError: If geometries are invalid or triangulation fails
        """
        pass
    
    def _normalize_geometries(
        self, 
        geometries: Union[Polygon, MultiPolygon, List[Polygon]]
    ) -> List[Polygon]:
        """
        Normalize input geometries to a list of polygons.
        
        Args:
            geometries: Input geometries in various formats
            
        Returns:
            List of Polygon objects
            
        Raises:
            ValueError: If input contains invalid geometries
        """
        if isinstance(geometries, Polygon):
            return [geometries]
        elif isinstance(geometries, MultiPolygon):
            return list(geometries.geoms)
        elif isinstance(geometries, list):
            for geom in geometries:
                if not isinstance(geom, Polygon):
                    raise ValueError(f"Expected Polygon, got {type(geom)}")
            return geometries
        else:
            raise ValueError(f"Unsupported geometry type: {type(geometries)}")
