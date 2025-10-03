"""Geometric utility functions for bathymesh."""

from typing import Tuple, List
import numpy as np
from shapely.geometry import Polygon

from ..data_structures import PolygonStats


def validate_heightmap(heightmap: np.ndarray) -> None:
    """
    Validate heightmap array.
    
    Args:
        heightmap: 2D numpy array to validate
        
    Raises:
        ValueError: If heightmap is invalid
    """
    if not isinstance(heightmap, np.ndarray):
        raise ValueError("Heightmap must be a numpy array")
    
    if heightmap.ndim != 2:
        raise ValueError(f"Heightmap must be 2D, got {heightmap.ndim}D")
    
    if heightmap.size == 0:
        raise ValueError("Heightmap cannot be empty")
    
    if not np.isfinite(heightmap).all():
        raise ValueError("Heightmap contains non-finite values")


def normalize_heightmap(heightmap: np.ndarray, target_range: Tuple[float, float] = (0.0, 1.0)) -> np.ndarray:
    """
    Normalize heightmap to target range.
    
    Args:
        heightmap: 2D numpy array to normalize
        target_range: Target (min, max) range
        
    Returns:
        Normalized heightmap
    """
    validate_heightmap(heightmap)
    
    min_val, max_val = target_range
    if min_val >= max_val:
        raise ValueError("Target range min must be less than max")
    
    # Handle constant heightmaps
    data_min, data_max = heightmap.min(), heightmap.max()
    if data_min == data_max:
        return np.full_like(heightmap, (min_val + max_val) / 2)
    
    # Normalize to [0, 1] then scale to target range
    normalized = (heightmap - data_min) / (data_max - data_min)
    return normalized * (max_val - min_val) + min_val


def calculate_polygon_stats(polygons: List[Polygon]) -> PolygonStats:
    """
    Calculate statistics for a list of polygons.
    
    Args:
        polygons: List of Shapely Polygon objects
        
    Returns:
        PolygonStats dataclass with polygon statistics
    """
    if not polygons:
        return PolygonStats(
            count=0,
            total_area=0.0,
            mean_area=0.0,
            min_area=0.0,
            max_area=0.0,
        )
    
    areas = [poly.area for poly in polygons]
    
    return PolygonStats(
        count=len(polygons),
        total_area=sum(areas),
        mean_area=np.mean(areas),
        min_area=min(areas),
        max_area=max(areas),
    )


def create_test_heightmap(
    width: int = 50, 
    height: int = 50, 
    feature_scale: float = 10.0,
    noise_level: float = 0.1
) -> np.ndarray:
    """
    Create a test heightmap with interesting features.
    
    Args:
        width: Width of heightmap
        height: Height of heightmap
        feature_scale: Scale factor for main features
        noise_level: Level of random noise to add
        
    Returns:
        2D numpy array heightmap
    """
    x = np.linspace(-feature_scale/2, feature_scale/2, width)
    y = np.linspace(-feature_scale/2, feature_scale/2, height)
    X, Y = np.meshgrid(x, y)
    
    # Create heightmap with multiple features
    heightmap = (
        3 * np.exp(-(X**2 + Y**2) / (feature_scale**2 / 4)) +  # Central peak
        2 * np.exp(-((X-feature_scale/4)**2 + (Y-feature_scale/4)**2) / (feature_scale**2 / 8)) +  # Secondary peak
        1 * np.exp(-((X+feature_scale/4)**2 + (Y+feature_scale/8)**2) / (feature_scale**2 / 6)) +  # Another feature
        0.5 * np.sin(X * 2 * np.pi / feature_scale) * np.cos(Y * 2 * np.pi / feature_scale)  # Periodic component
    )
    
    # Add noise if requested
    if noise_level > 0:
        noise = np.random.normal(0, noise_level, heightmap.shape)
        heightmap += noise
    
    return heightmap
