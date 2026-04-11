import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np
import open3d as o3d
from bathy.python.bathy.config import MeshGenerationConfig
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
        """Apply scaling and offset to heightmap data."""

        if self._post_processed:
            logger.debug("Post-processing already applied, skipping")
            return

        logger.debug("Post-processing heightmap data with scaling and offset")

        self.data = (
            self.data * config.heightmap_processing.mesh_units.units_z
        ) + config.heightmap_processing.data_offset

        if config.heightmap_processing.exterior_buffer_width > 0:
            self.data = np.pad(
                self.data,
                pad_width=config.heightmap_processing.exterior_buffer_width,
                mode="constant",
                constant_values=config.heightmap_processing.exterior_buffer_value,
            )


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
