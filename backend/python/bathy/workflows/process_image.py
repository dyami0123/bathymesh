from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np
from bathy.config import ProjectConfig
from bathy.image_processing.image_processor import ImageProcessor
from bathy.database_interface import DatabaseInterface


def process_image(
    image_path_or_data: Union[str, Path, bytes],
    project_config: ProjectConfig,
) -> np.ndarray:

    processor = ImageProcessor(config=project_config.image_processing)

    image = processor.load_image(
        image_path_or_data,
    )

    result = processor.process_image_to_heightmap(
        image,
    )

    return result
