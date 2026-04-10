#!/usr/bin/env python
"""
Example script demonstrating the ImageToHeightmapWorkflow class.

This shows the recommended workflow-based approach for converting images to heightmaps.
"""

import logging
from pathlib import Path

from backend.python.bathy.config import ImageProcessingConfig
from backend.python.bathy.workflows.process_image import process_image
from backend.python.bathy.viz.heightmap import heightmap_plot

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    data_dir = Path(__file__).parent.parent / "data"

    # Define your image path and color mapping
    image_path = data_dir / "raw" / "hawaii.jpg"
    save_path = data_dir / "processed" / "hawaii.npy"

    fuzz = 21.0  # Color matching tolerance

    color_map = {
        "#031f5c": {"value": -6, "fuzziness": fuzz},
        "#1729c6": {"value": -5.5, "fuzziness": fuzz},
        "#1a5af4": {"value": -5, "fuzziness": fuzz},
        "#0f8ff0": {"value": -4.5, "fuzziness": fuzz},
        "#44c4fe": {"value": -4, "fuzziness": fuzz},
        "#65e3eb": {"value": -3.5, "fuzziness": fuzz},
        "#74e3b0": {"value": -3, "fuzziness": fuzz},
        "#baf49c": {"value": -2.5, "fuzziness": fuzz},
        "#f0ee7d": {"value": -2, "fuzziness": fuzz},
        "#f39f43": {"value": -1.5, "fuzziness": fuzz},
        "#e65944": {"value": -1, "fuzziness": fuzz},
        "#fb6667": {"value": -0.5, "fuzziness": fuzz},
        "#f38785": {"value": 0, "fuzziness": fuzz},
        "#287202": {"value": 0.5, "fuzziness": fuzz},
        "#468325": {"value": 1, "fuzziness": fuzz},
        "#649949": {"value": 1.5, "fuzziness": fuzz},
        "#759e5b": {"value": 2, "fuzziness": fuzz},
        "#8aaa76": {"value": 2.5, "fuzziness": fuzz},
        "#b0c39f": {"value": 3, "fuzziness": fuzz},
        "#b1bda0": {"value": 3.5, "fuzziness": fuzz},
        "#9e995e": {"value": 4, "fuzziness": fuzz},
    }

    # invert order to have lowest colors first
    color_map = dict(reversed(list(color_map.items())))

    config = ImageProcessingConfig(
        preserve_full_resolution=True,
        max_dimension=None,
        region=(0.1, 0.1, 0.9, 0.9),
        fill_nan_values=True,
        fill_max_iterations=50,
        fill_neighborhood=1,
        color_map=color_map,
        default_fuzziness=30.0,
    )

    heightmap_data = process_image(
        image_path=image_path,
        config=config,
        save_path=save_path,
    )

    heightmap_plot(
        data=heightmap_data,
        save_path=data_dir / "processed" / "hawaii.png",
    )
