from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


@dataclass
class MeshUnits:
    """Scaling parameters for mesh generation."""

    units_x: float = 1.0
    units_y: float = 1.0
    units_z: float = 1.0


@dataclass
class HeighmapProcessingConfig:
    exterior_buffer_width: int = field(default=0)

    exterior_buffer_value: float = field(default=0.0)

    data_offset: float = field(default=0)

    mesh_units: MeshUnits = field(default_factory=MeshUnits)

    thresholds: list[float] = field(
        default_factory=lambda: [x for x in np.linspace(0, 50, 10)],
        metadata={"help": "List of height thresholds for each level"},
    )
    base_height: float = field(
        default=0.0,
        metadata={"help": "Z-coordinate of the base level"},
    )
    layer_thickness: float = field(
        default=0.5,
        metadata={"help": "Thickness of each extruded layer"},
    )


@dataclass
class MeshCombinationConfig:
    merge_threshold: float = field(
        default=1e-6,
        metadata={"help": "Threshold for merging close vertices when combining meshes"},
    )


@dataclass
class ContourExtractionConfig:
    min_polygon_area: float = field(
        default=1e-2,
        metadata={"help": "Minimum polygon area for contour extraction"},
    )
    simplify_tolerance: float = field(
        default=0.5,
        metadata={"help": "Tolerance for simplifying extracted contours"},
    )
    max_segments: int = field(
        default=100,
        metadata={"help": "Maximum number of segments for contour extraction"},
    )
    min_area_fraction: float = field(
        default=0.01,
        metadata={"help": "Minimum area fraction for contour extraction"},
    )


@dataclass
class TriangulationConfig:

    triangulator_add_interior_points: bool = field(
        default=True,
        metadata={"help": "Whether to add interior points during triangulation"},
    )
    triangulator_interior_point_density: float = field(
        default=1.0,
        metadata={"help": "Density of interior points (points per unit area)"},
    )


@dataclass
class PostProcessingConfig:
    apply_post_processing: bool = field(
        default=True,
        metadata={"help": "Whether to apply post-processing to meshes"},
    )
    remove_degenerate_triangles: bool = field(
        default=True,
        metadata={"help": "Remove degenerate triangles"},
    )
    remove_duplicated_vertices: bool = field(
        default=True,
        metadata={"help": "Remove duplicated vertices"},
    )
    remove_duplicated_triangles: bool = field(
        default=True,
        metadata={"help": "Remove duplicated triangles"},
    )
    remove_unreferenced_vertices: bool = field(
        default=True,
        metadata={"help": "Remove unreferenced vertices"},
    )
    merge_close_vertices: bool = field(
        default=False,
        metadata={"help": "Merge vertices that are very close"},
    )
    merge_vertices_threshold: float = field(
        default=1e-6,
        metadata={"help": "Distance threshold for merging vertices"},
    )
    simplification_method: str = field(
        default="none",
        metadata={"help": "Method for mesh simplification"},
    )
    target_triangle_count: int = field(
        default=100000,
        metadata={"help": "Target triangle count for mesh simplification"},
    )
    voxel_size: float = field(
        default=0.05,
        metadata={"help": "Voxel size for vertex clustering simplification"},
    )


@dataclass
class MeshGenerationConfig:

    stateless: bool = field(
        default=True,
        metadata={"help": "Whether to run in stateless mode (no visualizations)"},
    )

    heightmap_processing: HeighmapProcessingConfig = field(
        default_factory=HeighmapProcessingConfig,
    )
    mesh_combination: MeshCombinationConfig = field(
        default_factory=MeshCombinationConfig,
    )
    contour_extraction: ContourExtractionConfig = field(
        default_factory=ContourExtractionConfig,
    )
    triangulation: TriangulationConfig = field(
        default_factory=TriangulationConfig,
    )
    post_processing: PostProcessingConfig = field(
        default_factory=PostProcessingConfig,
    )


@dataclass
class ImageProcessingConfig:

    preserve_full_resolution: bool = field(
        default=True,
        metadata={"help": "Whether to preserve full image resolution"},
    )

    max_dimension: Optional[int] = field(
        default=None,
        metadata={"help": "Maximum dimension (width/height) for resizing images"},
    )

    region: Optional[tuple[int, int, int, int]] = field(
        default=None,
        metadata={
            "help": "Region of interest in the format (left, upper, right, lower)"
        },
    )

    fill_nan_values: bool = field(
        default=True,
        metadata={"help": "Whether to fill NaN values in images"},
    )

    fill_max_iterations: int = field(
        default=100,
        metadata={"help": "Maximum iterations for filling NaN values"},
    )
    fill_neighborhood: int = field(
        default=1,
        metadata={"help": "Neighborhood size for filling NaN values"},
    )

    color_map: OrderedDict = field(
        default_factory=lambda: OrderedDict(
            {
                "#0000FF": {"value": -10.0, "fuzziness": 5.0},  # Deep water
                "#00FFFF": {"value": -5.0, "fuzziness": 5.0},  # Shallow water
                "#00FF00": {"value": 0.0, "fuzziness": 5.0},  # Shoreline
                "#FFFF00": {"value": 5.0, "fuzziness": 5.0},  # Low land
                "#FF0000": {"value": 10.0, "fuzziness": 5.0},  # High land
            }
        ),
        metadata={"help": "Color to value mapping with fuzziness"},
    )
    default_fuzziness: float = field(
        default=10.0,
        metadata={"help": "Default fuzziness value (Delta E) when not specified"},
    )
