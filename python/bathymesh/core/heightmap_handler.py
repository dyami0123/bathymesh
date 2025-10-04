"""Heightmap data container and handler for mesh generation."""

from typing import List, Tuple, Callable, Optional, Union, TYPE_CHECKING
import numpy as np
from shapely.geometry import Polygon
import logging

from ..data_structures import MeshScaling

if TYPE_CHECKING:
    from .heightmap_processor import HeightmapProcessor

logger = logging.getLogger(__name__)


class HeightmapHandler:
    """
    Container and handler for heightmap data with methods for mesh generation.
    
    This class encapsulates heightmap data and provides methods to extract
    geometries and height information for different mesh generation approaches.
    """
    
    heightmap: np.ndarray
    x_coords: np.ndarray
    y_coords: np.ndarray
    scaling: MeshScaling
    processor: 'HeightmapProcessor'
    
    def __init__(
        self,
        heightmap: np.ndarray,
        x_coords: Optional[np.ndarray] = None,
        y_coords: Optional[np.ndarray] = None,
        scaling: Optional[MeshScaling] = None,
        processor: Optional['HeightmapProcessor'] = None
    ):
        """
        Initialize heightmap handler.
        
        Args:
            heightmap: 2D array of height values
            x_coords: 1D array of x-coordinates (optional, creates default grid)
            y_coords: 1D array of y-coordinates (optional, creates default grid)
            scaling: Scaling parameters for mesh generation
            processor: HeightmapProcessor instance for contour extraction
        """
        if heightmap.ndim != 2:
            raise ValueError(f"Heightmap must be 2D, got {heightmap.ndim}D")
            
        self.heightmap = heightmap
        self.scaling = scaling or MeshScaling()
        
        # Import here to avoid circular imports
        if processor is None:
            from .heightmap_processor import HeightmapProcessor
            self.processor = HeightmapProcessor()
        else:
            self.processor = processor
        
        height, width = heightmap.shape
        
        # Create default coordinate arrays if not provided
        if x_coords is None:
            self.x_coords = np.linspace(0, width - 1, width) * self.scaling.scale_x
        else:
            if len(x_coords) != width:
                raise ValueError(f"x_coords length {len(x_coords)} doesn't match heightmap width {width}")
            self.x_coords = x_coords
            
        if y_coords is None:
            self.y_coords = np.linspace(0, height - 1, height) * self.scaling.scale_y
        else:
            if len(y_coords) != height:
                raise ValueError(f"y_coords length {len(y_coords)} doesn't match heightmap height {height}")
            self.y_coords = y_coords
    
    @property
    def shape(self) -> Tuple[int, int]:
        """Get heightmap shape (height, width)."""
        return self.heightmap.shape
    
    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Get bounds as (min_x, min_y, max_x, max_y)."""
        return (
            self.x_coords.min(),
            self.y_coords.min(), 
            self.x_coords.max(),
            self.y_coords.max()
        )
    
    @property
    def height_range(self) -> Tuple[float, float]:
        """Get height range as (min_height, max_height)."""
        return (self.heightmap.min(), self.heightmap.max())
    
    def get_height_function(self) -> Callable[[float, float], float]:
        """
        Get a height function for interpolating height at any (x, y) coordinate.
        
        Returns:
            Function that takes (x, y) and returns interpolated height
        """
        from scipy.interpolate import RegularGridInterpolator
        
        interpolator = RegularGridInterpolator(
            (self.y_coords, self.x_coords),
            self.heightmap,
            method='linear',
            bounds_error=False,
            fill_value=0.0
        )
        
        def height_function(x: float, y: float) -> float:
            try:
                return float(interpolator((y, x)))
            except (ValueError, IndexError):
                return 0.0
        
        return height_function
    
    def extract_contour_polygons(self, threshold: float) -> List[Polygon]:
        """
        Extract polygons at a specific height threshold.
        
        Args:
            threshold: Height threshold for contour extraction
            
        Returns:
            List of Shapely Polygon objects
        """
        polygons = self.processor.extract_contour_polygons(self.heightmap, threshold)
        
        # Scale polygons to real-world coordinates
        scaled_polygons = []
        for poly in polygons:
            coords = np.array(poly.exterior.coords)
            # Convert from array indices to real coordinates
            scaled_coords = []
            for x_idx, y_idx in coords:
                real_x = self.x_coords[int(np.clip(x_idx, 0, len(self.x_coords) - 1))]
                real_y = self.y_coords[int(np.clip(y_idx, 0, len(self.y_coords) - 1))]
                scaled_coords.append((real_x, real_y))
            
            try:
                scaled_poly = Polygon(scaled_coords)
                if scaled_poly.is_valid:
                    scaled_polygons.append(scaled_poly)
            except Exception as e:
                logger.warning(f"Failed to create scaled polygon: {e}")
                continue
        
        return scaled_polygons
    
    def extract_multi_level_polygons(
        self, 
        thresholds: List[float]
    ) -> List[Tuple[float, List[Polygon]]]:
        """
        Extract polygons at multiple height thresholds.
        
        Args:
            thresholds: List of height thresholds
            
        Returns:
            List of (threshold, polygons) tuples
        """
        results = []
        for threshold in thresholds:
            polygons = self.extract_contour_polygons(threshold)
            results.append((threshold, polygons))
        return results
    
    def get_bounding_polygon(self) -> Polygon:
        """
        Get a polygon representing the full bounds of the heightmap.
        
        Returns:
            Shapely Polygon covering the entire heightmap area
        """
        min_x, min_y, max_x, max_y = self.bounds
        return Polygon([
            (min_x, min_y),
            (max_x, min_y), 
            (max_x, max_y),
            (min_x, max_y)
        ])
    
    def create_surface_mesh_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Create vertices and faces for a surface mesh representation.
        
        Returns:
            Tuple of (vertices, faces) arrays for surface mesh
        """
        return self.processor.create_simple_surface_mesh_data(self.heightmap, self.scaling)
    
    def get_height_at_points(self, points: np.ndarray) -> np.ndarray:
        """
        Get heights at specific (x, y) points using interpolation.
        
        Args:
            points: (N, 2) array of (x, y) coordinates
            
        Returns:
            (N,) array of interpolated heights
        """
        height_func = self.get_height_function()
        return np.array([height_func(x, y) for x, y in points])
    
    def get_stats(self) -> dict:
        """
        Get statistics about the heightmap.
        
        Returns:
            Dictionary with heightmap statistics
        """
        return {
            'shape': self.shape,
            'bounds': self.bounds,
            'height_range': self.height_range,
            'mean_height': self.heightmap.mean(),
            'std_height': self.heightmap.std(),
            'scaling': {
                'scale_x': self.scaling.scale_x,
                'scale_y': self.scaling.scale_y,
                'scale_z': self.scaling.scale_z
            }
        }
