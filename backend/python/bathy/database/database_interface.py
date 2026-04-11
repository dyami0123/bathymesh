from bathy.config import ProjectConfig
from typing import Any
import numpy as np
import logging


ImageData = Any
STLType = Any
logger = logging.getLogger(__name__)


class DatabaseInterfaceClass:

    def get_config(self, project_id: str) -> ProjectConfig:
        logger.debug(f"Getting config for project: {project_id}")
        return ProjectConfig()

    def set_config(self, project_id: str, project_config: ProjectConfig) -> None:
        logger.debug(f"Setting config for project: {project_id}")
        pass

    def set_image_data(self, project_id: str, image_data: ImageData) -> None:
        logger.debug(f"Setting image data for project: {project_id}")
        pass

    def get_image_data(self, project_id: str) -> ImageData:
        logger.debug(f"Getting image data for project: {project_id}")
        pass

    def set_heightmap_data(self, project_id: str, heightmap_data: np.ndarray) -> None:
        logger.debug(f"Setting heightmap data for project: {project_id}")
        pass

    def get_heightmap_data(self, project_id: str) -> np.ndarray:
        logger.debug(f"Getting heightmap data for project: {project_id}")
        return []

    def set_stl(self, project_id: str, stl_data: STLType) -> None:
        logger.debug(f"Setting STL data for project: {project_id}")
        pass

    def get_stl(self, project_id: Any) -> STLType:
        logger.debug(f"Getting STL data for project: {project_id}")
        pass


DatabaseInterface = DatabaseInterfaceClass()
