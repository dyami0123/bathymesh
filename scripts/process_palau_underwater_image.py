#!/usr/bin/env python
"""
Example script demonstrating the ImageToHeightmapWorkflow class.

This shows the recommended workflow-based approach for converting images to heightmaps.
"""

import logging
from pathlib import Path

import matplotlib.pyplot as plt
from bathymesh.workflows.process_image import process_image

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    data_dir = Path(__file__).parent.parent / "data"

    # Define your image path and color mapping
    image_path = data_dir / "raw" / "palau-bathymetry-map.png"
    save_path = data_dir / "processed" / "palau_heightmap_bathy.npy"

    gnd = 100  # Ground level reference
    fuzz = 30.0  # Color matching tolerance

    color_map = {
        "#69bd33": {"value": gnd, "fuzziness": fuzz},
        "#525315": {"value": gnd, "fuzziness": fuzz},
        "#ffeaba": {"value": gnd, "fuzziness": fuzz},
        "#e64500": {"value": gnd - 2.5, "fuzziness": fuzz},
        "#e69901": {"value": gnd - 7.5, "fuzziness": fuzz},
        "#cbeb01": {"value": gnd - 15, "fuzziness": fuzz},
        "#69f266": {"value": gnd - 25, "fuzziness": fuzz},
        "#6bf062": {"value": gnd - 25, "fuzziness": fuzz},
        "#14d4ab": {"value": gnd - 35, "fuzziness": fuzz},
        "#00a6c0": {"value": gnd - 45, "fuzziness": fuzz},
        "#0071bd": {"value": gnd - 62.5, "fuzziness": fuzz},
        "#064497": {"value": gnd - 77.5, "fuzziness": fuzz},
        "#08266e": {"value": gnd - 125, "fuzziness": fuzz},
        "#000f4a": {"value": gnd - 150, "fuzziness": fuzz},
        "#1e88d1": {"value": gnd - 62.5, "fuzziness": fuzz},
        "#9ba7e3": {"value": gnd - 80, "fuzziness": fuzz},
        "#928ecd": {"value": gnd - 100, "fuzziness": fuzz},
        "#9a85cc": {"value": gnd - 120, "fuzziness": fuzz},
        "#a85ef9": {"value": gnd - 150, "fuzziness": fuzz},
        "#101320": {"value": gnd - 200, "fuzziness": 30.0},
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
    plt.savefig(data_dir / "processed" / "palau_heightmap.png")
