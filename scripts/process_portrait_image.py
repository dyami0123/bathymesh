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

    project_name = "portrait_jan_26"
    source_image = "portrait_jan_26"
    # source_image = project_name

    # Define your image path and color mapping
    image_path = data_dir / "raw" / f"{source_image}.png"
    save_path = data_dir / "processed" / f"{project_name}.npy"

    fuzz = 20 # Color matching tolerance

    color_map = {
        
        "#FFFFFF": {"value": 1, "fuzziness": fuzz},
        
        
        "#D6FF8A": {"value": 2, "fuzziness": fuzz},
        "#CDFF8C": {"value": 2, "fuzziness": fuzz},
        
        
        "#365E24": {"value": -1, "fuzziness": fuzz},
        "#8AD78A": {"value": 2, "fuzziness": fuzz},
        "#65CD42": {"value": 2, "fuzziness": fuzz},
        
        
        "#6A003F": {"value": 5, "fuzziness": fuzz},
        "#780033": {"value": 5, "fuzziness": fuzz},
        
        "#B6024E": {"value": 6, "fuzziness": fuzz},
        "#B12870": {"value": 6, "fuzziness": fuzz},
        
        
        "#F8FF41": {"value": 2, "fuzziness": fuzz}, 
        
        "#350019": {"value": 4, "fuzziness": fuzz},
        "#150010": {"value": 4, "fuzziness": fuzz},
        "#130014": {"value": 4, "fuzziness": fuzz},
        
        
        "#97D7C8": {"value": -1, "fuzziness": fuzz},
        "#94FFC8": {"value": -1, "fuzziness": fuzz},
        
        
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
