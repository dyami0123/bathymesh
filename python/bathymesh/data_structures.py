"""Data classes and enums for bathymesh structures."""

from dataclasses import dataclass
from typing import List, Union, TYPE_CHECKING
from pathlib import Path
from enum import Enum

if TYPE_CHECKING:
    import numpy as np


class MeshFormat(Enum):
    """Supported mesh file formats."""
    STL = '.stl'
    PLY = '.ply'
    OBJ = '.obj'
    OFF = '.off'
    
    @classmethod
    def from_extension(cls, extension: str) -> 'MeshFormat':
        """Get MeshFormat from file extension."""
        ext = extension.lower().strip()
        if not ext.startswith('.'):
            ext = f'.{ext}'
        
        for format_enum in cls:
            if format_enum.value == ext:
                return format_enum
        
        raise ValueError(f"Unsupported format '{ext}'. Supported: {', '.join([f.value for f in cls])}")
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of all supported file extensions."""
        return [f.value for f in cls]


class MeshType(Enum):
    """Supported mesh generation types."""
    FLAT = "flat"
    EXTRUDED = "extruded"
    SURFACE = "surface"
    CONTOUR = "contour"


@dataclass
class PolygonStats:
    """Statistics for a collection of polygons."""
    count: int
    total_area: float
    mean_area: float
    min_area: float
    max_area: float


@dataclass 
class MeshInfo:
    """Information about a mesh."""
    num_vertices: int
    num_triangles: int
    has_vertex_normals: bool
    has_triangle_normals: bool
    is_watertight: bool
    is_orientable: bool
    bounding_box_min: Union[List[float], None] = None
    bounding_box_max: Union[List[float], None] = None
    bounding_box_extent: Union[List[float], None] = None


@dataclass
class MeshScaling:
    """Scaling parameters for mesh generation."""
    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0


