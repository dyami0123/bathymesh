# Bathymesh package - wrapper for bathy module
# This allows importing as 'bathymesh' while the actual code is in 'bathy'

# Note: This is a compatibility layer. The actual implementation is in the 'bathy' module.
# Some imports may fail if the corresponding modules don't exist yet.

__version__ = "0.1.0"

# Re-export everything from bathy
from bathy import *

# Try to import commonly used items
try:
    from bathy.config import MeshGenerationConfig, ImageProcessingConfig
except ImportError:
    pass

try:
    from bathy.data_model import HeightmapData, MeshData
except ImportError:
    pass

try:
    from bathy.mesh_generator import MeshGenerator
except ImportError:
    pass

__all__ = []
