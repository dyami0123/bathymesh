"""Utility functions for bathymesh."""

from .geometry import (
    validate_heightmap,
    normalize_heightmap, 
    calculate_polygon_stats,
    create_test_heightmap
)

__all__ = [
    "validate_heightmap",
    "normalize_heightmap", 
    "calculate_polygon_stats",
    "create_test_heightmap"
]
