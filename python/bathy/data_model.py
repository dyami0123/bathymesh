import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import open3d as o3d
from bathy.config import MeshGenerationConfig
from shapely.geometry import Polygon

logger = logging.getLogger(__name__)


@dataclass
class RawHeightmapData:
    data: np.ndarray

    @property
    def shape(self) -> tuple[int, int]:
        return self.data.shape


@dataclass
class HeightmapData:
    data: np.ndarray
    _post_processed: bool = False

    def post_process(self, config: MeshGenerationConfig) -> None:
        """Apply scaling and offset to heightmap data.

        The offset is applied FIRST to shift the data (e.g., to make all values positive),
        then the z scale factor is applied to convert to final mesh units.

        When heightmap splitting is enabled, the exterior buffer is NOT applied
        here - it will be applied to each tile individually in the mesh generator.
        This ensures each tile gets its own buffer for proper contour extraction.
        """

        if self._post_processed:
            logger.debug("Post-processing already applied, skipping")
            return

        logger.debug("Post-processing heightmap data with scaling and offset")

        # Apply offset first (e.g., to shift negative values to start at 0)
        # Then apply z scale factor to convert to final mesh units
        self.data = (
            self.data + config.heightmap_processing.data_offset
        ) * config.heightmap_processing.mesh_units.units_z

        # Only add buffer here if NOT using heightmap-based tiling
        # When tiling is enabled, each tile gets its own buffer in _generate_tile_mesh()
        if (
            config.heightmap_processing.exterior_buffer_width > 0
            and not config.heightmap_splitting.enabled
        ):
            self.data = np.pad(
                self.data,
                pad_width=config.heightmap_processing.exterior_buffer_width,
                mode="constant",
                constant_values=config.heightmap_processing.exterior_buffer_value,
            )

        self._post_processed = True


@dataclass
class MeshData:
    data: o3d.geometry.TriangleMesh


@dataclass
class ThresholdSnapshot:
    threshold: float
    mesh: Optional[o3d.geometry.TriangleMesh] = None
    contours: Optional[list[Polygon]] = None
    vertices_2d: Optional[list[np.ndarray]] = None
    triangles: Optional[list[np.ndarray]] = None


@dataclass
class SplitMeshResult:
    """Result of mesh generation with optional splitting.

    Supports both:
    - Heightmap-based splitting (tiles): meshes are generated per-tile
    - Mesh-based splitting (deprecated): combined mesh is split after generation
    """

    combined_mesh: o3d.geometry.TriangleMesh
    split_meshes: list[o3d.geometry.TriangleMesh]
    split_planes: list[tuple[tuple[float, float, float], tuple[float, float, float]]]

    # Tile information (for heightmap-based splitting)
    tile_ids: list[str] = field(
        default_factory=list
    )  # e.g., ["r0c0", "r0c1", "r1c0", "r1c1"]
    tile_grid: tuple[int, int] = (1, 1)  # (rows, cols)

    @property
    def has_splits(self) -> bool:
        """Check if the mesh was split."""
        return len(self.split_meshes) > 0

    @property
    def has_tiles(self) -> bool:
        """Check if the result has tile information."""
        return len(self.tile_ids) > 0

    @property
    def num_pieces(self) -> int:
        """Number of split pieces (0 if not split)."""
        return len(self.split_meshes)

    def get_tile_mesh(self, row: int, col: int) -> Optional[o3d.geometry.TriangleMesh]:
        """Get mesh for a specific tile position."""
        tile_id = f"r{row}c{col}"
        if tile_id in self.tile_ids:
            idx = self.tile_ids.index(tile_id)
            if idx < len(self.split_meshes):
                return self.split_meshes[idx]
        return None
