"""Configuration serialization and deserialization for YAML files.

This module handles converting between bathymesh config dataclasses and YAML format.
All configs are saved with complete default values for transparency.
"""

import logging
from collections import OrderedDict
from pathlib import Path
from typing import Any, Union

import yaml

from bathy.config import (
    ContourExtractionConfig,
    HeighmapProcessingConfig,
    ImageProcessingConfig,
    MeshCombinationConfig,
    MeshGenerationConfig,
    MeshUnits,
    PostProcessingConfig,
    TriangulationConfig,
)

logger = logging.getLogger(__name__)


class ConfigIOError(Exception):
    """Exception raised for config I/O errors."""

    pass


def _represent_ordereddict(dumper: yaml.Dumper, data: OrderedDict) -> yaml.Node:
    """Custom YAML representer for OrderedDict to maintain insertion order."""
    return dumper.represent_mapping("tag:yaml.org,2002:map", data.items())


def _construct_ordereddict(loader: yaml.Loader, node: yaml.Node) -> OrderedDict:
    """Custom YAML constructor for OrderedDict."""
    return OrderedDict(loader.construct_pairs(node))


# Register custom OrderedDict handlers
yaml.add_representer(OrderedDict, _represent_ordereddict)
yaml.add_constructor(
    "tag:yaml.org,2002:map", _construct_ordereddict, Loader=yaml.SafeLoader
)


def config_to_dict(
    config: Union[ImageProcessingConfig, MeshGenerationConfig],
) -> dict[str, Any]:
    """Convert a config dataclass to a dictionary suitable for YAML serialization.

    Args:
        config: Configuration object to convert

    Returns:
        Dictionary representation of the config
    """
    if isinstance(config, ImageProcessingConfig):
        return {
            "preserve_full_resolution": config.preserve_full_resolution,
            "max_dimension": config.max_dimension,
            "region": list(config.region) if config.region else None,
            "fill_nan_values": config.fill_nan_values,
            "fill_max_iterations": config.fill_max_iterations,
            "fill_neighborhood": config.fill_neighborhood,
            "color_map": dict(config.color_map),  # OrderedDict to dict
            "default_fuzziness": config.default_fuzziness,
        }
    elif isinstance(config, MeshGenerationConfig):
        return {
            "stateless": config.stateless,
            "heightmap_processing": {
                "exterior_buffer_width": config.heightmap_processing.exterior_buffer_width,
                "exterior_buffer_value": config.heightmap_processing.exterior_buffer_value,
                "data_offset": config.heightmap_processing.data_offset,
                "mesh_units": {
                    "units_x": config.heightmap_processing.mesh_units.units_x,
                    "units_y": config.heightmap_processing.mesh_units.units_y,
                    "units_z": config.heightmap_processing.mesh_units.units_z,
                },
                "thresholds": [
                    float(x) for x in config.heightmap_processing.thresholds
                ],
                "base_height": config.heightmap_processing.base_height,
                "layer_thickness": config.heightmap_processing.layer_thickness,
            },
            "contour_extraction": {
                "min_polygon_area": config.contour_extraction.min_polygon_area,
                "simplify_tolerance": config.contour_extraction.simplify_tolerance,
                "max_segments": config.contour_extraction.max_segments,
                "min_area_fraction": config.contour_extraction.min_area_fraction,
            },
            "mesh_combination": {
                "merge_threshold": config.mesh_combination.merge_threshold,
            },
            "triangulation": {
                "triangulator_add_interior_points": config.triangulation.triangulator_add_interior_points,
                "triangulator_interior_point_density": config.triangulation.triangulator_interior_point_density,
            },
            "post_processing": {
                "apply_post_processing": config.post_processing.apply_post_processing,
                "remove_degenerate_triangles": config.post_processing.remove_degenerate_triangles,
                "remove_duplicated_vertices": config.post_processing.remove_duplicated_vertices,
                "remove_duplicated_triangles": config.post_processing.remove_duplicated_triangles,
                "remove_unreferenced_vertices": config.post_processing.remove_unreferenced_vertices,
                "merge_close_vertices": config.post_processing.merge_close_vertices,
                "merge_vertices_threshold": config.post_processing.merge_vertices_threshold,
                "simplification_method": config.post_processing.simplification_method,
                "target_triangle_count": config.post_processing.target_triangle_count,
                "voxel_size": config.post_processing.voxel_size,
            },
        }
    else:
        raise ConfigIOError(f"Unsupported config type: {type(config)}")


def dict_to_image_config(data: dict[str, Any]) -> ImageProcessingConfig:
    """Convert a dictionary to an ImageProcessingConfig.

    Args:
        data: Dictionary representation of the config

    Returns:
        ImageProcessingConfig object

    Raises:
        ConfigIOError: If required fields are missing or invalid
    """
    try:
        # Convert color_map back to OrderedDict
        color_map = OrderedDict(data.get("color_map", {}))

        # Convert region tuple if present
        region = tuple(data["region"]) if data.get("region") else None

        return ImageProcessingConfig(
            preserve_full_resolution=data.get("preserve_full_resolution", True),
            max_dimension=data.get("max_dimension"),
            region=region,
            fill_nan_values=data.get("fill_nan_values", True),
            fill_max_iterations=data.get("fill_max_iterations", 100),
            fill_neighborhood=data.get("fill_neighborhood", 1),
            color_map=color_map,
            default_fuzziness=data.get("default_fuzziness", 10.0),
        )
    except Exception as e:
        raise ConfigIOError(f"Failed to parse ImageProcessingConfig: {e}")


def dict_to_mesh_config(data: dict[str, Any]) -> MeshGenerationConfig:
    """Convert a dictionary to a MeshGenerationConfig.

    Args:
        data: Dictionary representation of the config

    Returns:
        MeshGenerationConfig object

    Raises:
        ConfigIOError: If required fields are missing or invalid
    """
    try:
        hp_data = data.get("heightmap_processing", {})
        ce_data = data.get("contour_extraction", {})
        mc_data = data.get("mesh_combination", {})
        tr_data = data.get("triangulation", {})
        pp_data = data.get("post_processing", {})

        # Build nested configs
        mesh_units = MeshUnits(
            units_x=hp_data.get("mesh_units", {}).get("units_x", 1.0),
            units_y=hp_data.get("mesh_units", {}).get("units_y", 1.0),
            units_z=hp_data.get("mesh_units", {}).get("units_z", 1.0),
        )

        # Ensure thresholds are converted to regular floats (not numpy scalars)
        thresholds_raw = hp_data.get("thresholds", [x for x in range(0, 50, 10)])
        thresholds = [float(x) for x in thresholds_raw]

        heightmap_processing = HeighmapProcessingConfig(
            exterior_buffer_width=hp_data.get("exterior_buffer_width", 0),
            exterior_buffer_value=hp_data.get("exterior_buffer_value", 0.0),
            data_offset=hp_data.get("data_offset", 0),
            mesh_units=mesh_units,
            thresholds=thresholds,
            base_height=hp_data.get("base_height", 0.0),
            layer_thickness=hp_data.get("layer_thickness", 0.5),
        )

        contour_extraction = ContourExtractionConfig(
            min_polygon_area=ce_data.get("min_polygon_area", 1e-2),
            simplify_tolerance=ce_data.get("simplify_tolerance", 0.5),
            max_segments=ce_data.get("max_segments", 100),
            min_area_fraction=ce_data.get("min_area_fraction", 0.01),
        )

        mesh_combination = MeshCombinationConfig(
            merge_threshold=mc_data.get("merge_threshold", 1e-6),
        )

        triangulation = TriangulationConfig(
            triangulator_add_interior_points=tr_data.get(
                "triangulator_add_interior_points", True
            ),
            triangulator_interior_point_density=tr_data.get(
                "triangulator_interior_point_density", 1.0
            ),
        )

        post_processing = PostProcessingConfig(
            apply_post_processing=pp_data.get("apply_post_processing", True),
            remove_degenerate_triangles=pp_data.get(
                "remove_degenerate_triangles", True
            ),
            remove_duplicated_vertices=pp_data.get("remove_duplicated_vertices", True),
            remove_duplicated_triangles=pp_data.get(
                "remove_duplicated_triangles", True
            ),
            remove_unreferenced_vertices=pp_data.get(
                "remove_unreferenced_vertices", True
            ),
            merge_close_vertices=pp_data.get("merge_close_vertices", False),
            merge_vertices_threshold=pp_data.get("merge_vertices_threshold", 1e-6),
            simplification_method=pp_data.get("simplification_method", "none"),
            target_triangle_count=pp_data.get("target_triangle_count", 100000),
            voxel_size=pp_data.get("voxel_size", 0.05),
        )

        return MeshGenerationConfig(
            stateless=data.get("stateless", True),
            heightmap_processing=heightmap_processing,
            contour_extraction=contour_extraction,
            mesh_combination=mesh_combination,
            triangulation=triangulation,
            post_processing=post_processing,
        )
    except Exception as e:
        raise ConfigIOError(f"Failed to parse MeshGenerationConfig: {e}")


def config_to_yaml(config: Union[ImageProcessingConfig, MeshGenerationConfig]) -> str:
    """Convert a config to YAML string.

    Args:
        config: Configuration object to serialize

    Returns:
        YAML string representation
    """
    config_dict = config_to_dict(config)
    return yaml.dump(config_dict, default_flow_style=False, sort_keys=False)


def yaml_to_config(
    yaml_str: str, config_type: str
) -> Union[ImageProcessingConfig, MeshGenerationConfig]:
    """Convert YAML string to config object.

    Args:
        yaml_str: YAML string to parse
        config_type: Type of config ("image" or "mesh")

    Returns:
        Parsed config object

    Raises:
        ConfigIOError: If parsing fails or invalid config type
    """
    try:
        data = yaml.safe_load(yaml_str)

        if config_type == "image":
            return dict_to_image_config(data)
        elif config_type == "mesh":
            return dict_to_mesh_config(data)
        else:
            raise ConfigIOError(f"Invalid config type: {config_type}")

    except yaml.YAMLError as e:
        error_msg = str(e)
        if "numpy" in error_msg and "scalar" in error_msg:
            raise ConfigIOError(
                f"Config file contains numpy scalar objects that cannot be loaded. "
                f"This may be from an older version. Please delete the config file "
                f"and it will be recreated with correct format. Error: {e}"
            )
        raise ConfigIOError(f"Failed to parse YAML: {e}")


def save_config(
    config: Union[ImageProcessingConfig, MeshGenerationConfig], filepath: Path
) -> None:
    """Save config to YAML file.

    Args:
        config: Configuration object to save
        filepath: Path to save the config file

    Raises:
        ConfigIOError: If saving fails
    """
    try:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        yaml_content = config_to_yaml(config)
        filepath.write_text(yaml_content)
        logger.info(f"Saved config to {filepath}")
    except Exception as e:
        raise ConfigIOError(f"Failed to save config to {filepath}: {e}")


def load_config(
    filepath: Path, config_type: str
) -> Union[ImageProcessingConfig, MeshGenerationConfig]:
    """Load config from YAML file.

    Args:
        filepath: Path to the config file
        config_type: Type of config ("image" or "mesh")

    Returns:
        Loaded config object

    Raises:
        ConfigIOError: If loading or parsing fails
    """
    try:
        if not filepath.exists():
            raise ConfigIOError(f"Config file not found: {filepath}")

        yaml_content = filepath.read_text()
        return yaml_to_config(yaml_content, config_type)

    except Exception as e:
        if isinstance(e, ConfigIOError):
            raise
        raise ConfigIOError(f"Failed to load config from {filepath}: {e}")
