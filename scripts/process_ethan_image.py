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

    project_name = "ethan_profile"
    source_image = "ethan"
    # source_image = project_name

    # Define your image path and color mapping
    image_path = data_dir / "raw" / f"{source_image}.png"
    save_path = data_dir / "processed" / f"{project_name}.npy"

    fuzz = 20 # Color matching tolerance

    color_map = {
        
        "#C6C8B3": {"value": 1, "fuzziness": fuzz},
        "#7B7C70": {"value": 1.25, "fuzziness": fuzz},
        
        
        "#564139": {"value": 1.25, "fuzziness": fuzz},
        "#121011": {"value": 1.25, "fuzziness": fuzz},
        
        "#8C4E3F": {"value": 1.5, "fuzziness": fuzz},
        "#B9725D": {"value": 2, "fuzziness": fuzz},
        
        "#C91237": {"value": 1.25, "fuzziness": fuzz+10},
        "#5C0C23": {"value": 1, "fuzziness": fuzz-10},
        
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
        # fill_nan_approach="random"
    )
    
    heightmap_data = process_image(
        image_path=image_path,
        config=config,
        save_path=save_path,
    )
    
    heightmap_plot(
        data=heightmap_data,
        save_path=data_dir / "processed" / f"{project_name}.png",
    )
