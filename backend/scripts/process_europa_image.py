import logging
from pathlib import Path

from bathy.workflows.process_image import process_image
from bathy.config import ImageProcessingConfig
from bathy.viz.heightmap import heightmap_plot

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

    config = ImageProcessingConfig(
        preserve_full_resolution=True,
        max_dimension=None,
        region=None,
        fill_nan_values=True,
        fill_max_iterations=100,
        fill_neighborhood=1,
        color_map=color_map,
        default_fuzziness=fuzz,
    )

    heightmap_data = process_image(
        image_path=image_path,
        config=config,
        save_path=save_path,
    )

    heightmap_plot(
        data=heightmap_data,
        save_path=data_dir / "processed" / "europa.png",
    )
