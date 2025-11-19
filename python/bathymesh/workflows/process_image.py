from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np

from bathymesh.config import ImageConfig
from bathymesh.data_model import RawHeightmapData
from bathymesh.image_processing.image_processor import ImageProcessor


def process_image(
    image_path: Union[str, Path],
    config: ImageConfig,
    save_path: Union[str, Path, None] = None,
) -> RawHeightmapData:
    processor = ImageProcessor()

    image = processor.load_image(
        image_path,
        preserve_full_resolution=config.source.preserve_full_resolution,
        max_dimension=config.source.max_dimension,
    )

    heightmap_data = processor.process_image_to_heightmap(
        image,
        color_map=config.processing.color_map,
        default_fuzziness=config.processing.default_fuzziness,
        region=config.source.region,
        fill_nan_values=config.processing.fill_nan_values,
        fill_max_iterations=config.processing.fill_max_iterations,
        fill_neighborhood_size=config.processing.fill_neighborhood_size,
    )
    
    if save_path is not None:
        save_path = Path(save_path)
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, "wb") as f:
            np.save(f, heightmap_data)

    return RawHeightmapData(
        data=heightmap_data,
    )
