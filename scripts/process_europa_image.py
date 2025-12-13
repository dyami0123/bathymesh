#!/usr/bin/env python
"""
Example script demonstrating the ImageToHeightmapWorkflow class.

This shows the recommended workflow-based approach for converting images to heightmaps.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
from bathy.workflows.process_image import process_image

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    data_dir = Path(__file__).parent.parent / "data"

    # Define your image path and color mapping
    image_path = data_dir / "raw" / "europa.jpg"
    save_path = data_dir / "processed" / "europa.npy"

    fuzz = 21.0  # Color matching tolerance

    color_map = {
        "#cdcdcd": {"value": 50, "fuzziness": fuzz},
        "#888888": {"value": 50, "fuzziness": fuzz},
        "#7e7e7e": {"value": 50, "fuzziness": fuzz},
        "#5f5f5f": {"value": 20, "fuzziness": fuzz},
        "#252525": {"value": 20, "fuzziness": fuzz},
    }

    # invert order to have lowest colors first
    color_map = dict(reversed(list(color_map.items())))

    result = process_image(
        image_path=image_path,
        color_map=color_map,
        save_path=save_path,
        preserve_full_resolution=True,
        default_fuzziness=30.0,
        fill_nan_values=True,
        fill_max_iterations=50,
        fill_neighborhood_size=1,
    )

    plt.figure(figsize=(10, 8))
    plt.imshow(result.data, cmap="viridis", interpolation="nearest")
    plt.colorbar(label="Height")
    plt.title("Generated Heightmap")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.tight_layout()
    plt.savefig(data_dir / "processed" / "europa.png")
