from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np
from bathy.config import ImageProcessingConfig
from bathy.data_model import RawHeightmapData
from bathy.image_processing.image_processor import ImageProcessor


def process_image(
    image_path: Union[str, Path],
    config: ImageProcessingConfig,
    save_path: Union[None, Path] = None,
) -> np.ndarray:

    processor = ImageProcessor(config=config)

    image = processor.load_image(
        image_path,
    )

    result = processor.process_image_to_heightmap(
        image,
    )

    if save_path is not None:
        with open(save_path, "wb") as f:
            np.save(f, result)

    return result
