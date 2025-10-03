"""Heightmap processing functionality for bathymesh."""

from typing import List, Tuple, Union
import numpy as np
from skimage import measure
from shapely.geometry import Polygon
import logging

from ..data_structures import MeshScaling

logger = logging.getLogger(__name__)


class HeightmapProcessor:
    """Processes 2D heightmaps to extract contours and generate polygons."""
    
    min_polygon_area: float
    
    def __init__(self, min_polygon_area: float = 1e-2):
        """
        Initialize heightmap processor.
        
        Args:
            min_polygon_area: Minimum area threshold for valid polygons
        """
        self.min_polygon_area = min_polygon_area
    
    def extract_contour_polygons(
        self, 
        heightmap: np.ndarray, 
        threshold: float
    ) -> List[Polygon]:
        """
        Extract closed polygons from heightmap at given threshold.
        
        Args:
            heightmap: 2D numpy array of height values
            threshold: Height threshold for contour extraction
            
        Returns:
            List of valid Shapely Polygon objects
            
        Raises:
            ValueError: If heightmap is not 2D or threshold is invalid
        """
        if heightmap.ndim != 2:
            raise ValueError(f"Heightmap must be 2D, got {heightmap.ndim}D")
        
        logger.debug(f"Extracting contours at threshold {threshold}")
        
        try:
            contours = measure.find_contours(heightmap, threshold)
        except Exception as e:
            raise ValueError(f"Failed to extract contours: {e}") from e
        
        polygons = []
        for i, contour in enumerate(contours):
            try:
                polygon = self._contour_to_polygon(contour)
                if polygon and self._is_valid_polygon(polygon):
                    polygons.append(polygon)
                    logger.debug(f"Added polygon {i} with area {polygon.area:.3f}")
                else:
                    logger.debug(f"Skipped invalid polygon {i}")
            except Exception as e:
                logger.warning(f"Failed to process contour {i}: {e}")
                continue
        
        logger.info(f"Extracted {len(polygons)} valid polygons at threshold {threshold}")
        return polygons
    
    def extract_multi_level_polygons(
        self, 
        heightmap: np.ndarray, 
        thresholds: List[float]
    ) -> List[Tuple[float, List[Polygon]]]:
        """
        Extract polygons at multiple threshold levels.
        
        Args:
            heightmap: 2D numpy array of height values
            thresholds: List of height thresholds
            
        Returns:
            List of (threshold, polygons) tuples
        """
        results = []
        for threshold in thresholds:
            polygons = self.extract_contour_polygons(heightmap, threshold)
            results.append((threshold, polygons))
        
        return results
    
    def create_simple_surface_mesh_data(
        self, 
        heightmap: np.ndarray, 
        scaling: MeshScaling = MeshScaling()
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create vertices and faces for a simple surface mesh from heightmap.
        
        Args:
            heightmap: 2D numpy array of height values
            scaling: MeshScaling dataclass with scaling factors for each dimension
            
        Returns:
            Tuple of (vertices, faces) arrays
        """
        height, width = heightmap.shape
        
        # Create vertices
        vertices = []
        for i in range(height):
            for j in range(width):
                x = j * scaling.scale_x
                y = i * scaling.scale_y
                z = heightmap[i, j] * scaling.scale_z
                vertices.append([x, y, z])
        
        vertices = np.array(vertices)
        
        # Create triangular faces
        faces = []
        for i in range(height - 1):
            for j in range(width - 1):
                # Two triangles per grid cell
                v1 = i * width + j
                v2 = i * width + (j + 1)
                v3 = (i + 1) * width + j
                v4 = (i + 1) * width + (j + 1)
                
                # First triangle
                faces.append([v1, v2, v3])
                # Second triangle
                faces.append([v2, v4, v3])
        
        return vertices, np.array(faces)
    
    def _contour_to_polygon(self, contour: np.ndarray) -> Union[Polygon, None]:
        """
        Convert contour to Shapely polygon.
        
        Args:
            contour: Contour coordinates from skimage
            
        Returns:
            Shapely Polygon or None if conversion fails
        """
        if len(contour) < 3:
            return None
            
        # Flip axis to get (x, y) instead of (row, col)
        coords = np.flip(contour, axis=1)
        
        try:
            return Polygon(coords)
        except Exception:
            return None
    
    def _is_valid_polygon(self, polygon: Polygon) -> bool:
        """
        Check if polygon meets validity criteria.
        
        Args:
            polygon: Shapely Polygon to validate
            
        Returns:
            True if polygon is valid and meets area threshold
        """
        return (polygon.is_valid and 
                polygon.area > self.min_polygon_area)
