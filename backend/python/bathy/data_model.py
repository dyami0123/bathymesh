import logging
from datetime import datetime
from typing import Optional, Any, Literal, Union

import numpy as np
import open3d as o3d  # type: ignore
from pydantic import BaseModel, ConfigDict
from shapely.geometry import Polygon  # type: ignore

from bathy.config import MeshGenerationConfig

logger = logging.getLogger(__name__)


class HeightmapDataJson(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: list[list[float]]

    @classmethod
    def convert(cls, data: "HeightmapData") -> "HeightmapDataJson":
        """Convert from API output format to internal format."""
        return cls(data=data.data.tolist())


class HeightmapData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: np.ndarray

    _post_processed: bool = False

    @classmethod
    def convert(cls, api_result: HeightmapDataJson) -> "HeightmapData":
        """Convert from API output format to internal format."""
        return cls(data=np.array(api_result.data, dtype=np.float32))

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
        self._post_processed = True


class ImageData(BaseModel):
    data: bytes
    type: Literal["image/png", "image/jpeg", "image/tiff"]


class JobStatus(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    jobId: str
    status: Literal["pending", "processing", "completed", "failed"]
    jobType: str
    createdAt: datetime
    startedAt: Union[datetime, None] = None
    completedAt: Union[datetime, None] = None
    error: Union[str, None] = None
    result: Union[dict[str, Any], None] = None


class MeshData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    data: o3d.geometry.TriangleMesh


class MeshDataJson(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    vertices: list[list[float]]
    triangles: list[list[int]]

    @classmethod
    def convert(cls, mesh_data: MeshData) -> "MeshDataJson":
        """Convert from internal format to API output format."""
        vertices = np.asarray(mesh_data.data.vertices, dtype=np.float32).tolist()
        triangles = np.asarray(mesh_data.data.triangles, dtype=np.int32).tolist()
        return cls(vertices=vertices, triangles=triangles)


class ThresholdSnapshot(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    threshold: float
    mesh: Union[o3d.geometry.TriangleMesh, None] = None
    contours: Union[list[Polygon], None] = None
    vertices_2d: Union[list[np.ndarray], None] = None
    triangles: Union[list[np.ndarray], None] = None
