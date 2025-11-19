import logging
from dataclasses import dataclass, field

import numpy as np
import open3d as o3d

logger = logging.getLogger(__name__)


@dataclass
class RawHeightmapData:
    data: np.ndarray

    @property
    def shape(self) -> tuple[int, int]:
        return self.data.shape


@dataclass
class MeshUnits:
    """Scaling parameters for mesh generation."""

    units_x: float = 1.0
    units_y: float = 1.0
    units_z: float = 1.0


@dataclass
class HeightmapData:
    data: np.ndarray

    exterior_buffer_width: int = 0
    exterior_buffer_value: float = 0.0
    units: MeshUnits = field(default_factory=MeshUnits)

    data_offset: float = 0.0

    def post_process(self) -> None:
        """Apply scaling and offset to heightmap data."""
        logger.debug("Post-processing heightmap data with scaling and offset")

        self.data = (self.data * self.units.units_z) + self.data_offset

        if self.exterior_buffer_width > 0:
            self.data = np.pad(
                self.data,
                pad_width=self.exterior_buffer_width,
                mode="constant",
                constant_values=self.exterior_buffer_value,
            )


@dataclass
class MeshData:
    data: o3d.geometry.TriangleMesh
