from pathlib import Path
from typing import Dict, Optional, Tuple, Union

import numpy as np

from bathymesh.data_model import RawHeightmapData
from bathymesh.image_processing.image_processor import ImageProcessor


def process_image(
    image_path: Union[str, Path],
    color_map: Dict[str, Union[float, Dict]],
    save_path: Union[str, Path, None] = None,
    preserve_full_resolution: bool = True,
    max_dimension: Optional[int] = None,
    default_fuzziness: float = 10.0,
    region: Optional[Tuple[int, int, int, int]] = None,
    fill_nan_values: bool = False,
    fill_max_iterations: int = 100,
    fill_neighborhood_size: int = 1,
) -> RawHeightmapData:
    processor = ImageProcessor()

    image = processor.load_image(
        image_path,
        preserve_full_resolution=preserve_full_resolution,
        max_dimension=max_dimension,
    )

    heightmap_data = processor.process_image_to_heightmap(
        image,
        color_map=color_map,
        default_fuzziness=default_fuzziness,
        region=region,
        fill_nan_values=fill_nan_values,
        fill_max_iterations=fill_max_iterations,
        fill_neighborhood_size=fill_neighborhood_size,
    )
    save_path.parent.mkdir(parents=True, exist_ok=True)
    if save_path is not None:
        with open(save_path, "wb") as f:
            np.save(f, heightmap_data)

    return RawHeightmapData(
        data=heightmap_data,
    )
