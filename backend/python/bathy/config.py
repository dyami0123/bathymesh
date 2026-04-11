from collections import OrderedDict
from dataclasses import dataclass
from typing import Optional
from pydantic import BaseModel, Field

import numpy as np


class MeshUnits(BaseModel):
    """Scaling parameters for mesh generation."""

    units_x: float = 1.0
    units_y: float = 1.0
    units_z: float = 1.0


class HeighmapProcessingConfig(BaseModel):
    exterior_buffer_width: int = Field(default=0)

    exterior_buffer_value: float = Field(default=0.0)

    data_offset: float = Field(default=0)

    mesh_units: MeshUnits = Field(default_factory=MeshUnits)

    thresholds: list[float] = Field(
        default_factory=lambda: [x for x in np.linspace(0, 50, 10)],
        description="List of height thresholds for each level",
    )
    base_height: float = Field(
        default=0.0,
        description="Z-coordinate of the base level",
    )
    layer_thickness: float = Field(
        default=0.5,
        description="Thickness of each extruded layer",
    )


class MeshCombinationConfig(BaseModel):
    merge_threshold: float = Field(
        default=1e-6,
        description="Threshold for merging close vertices when combining meshes",
    )


class ContourExtractionConfig(BaseModel):
    min_polygon_area: float = Field(
        default=1e-2,
        description="Minimum polygon area for contour extraction",
    )
    simplify_tolerance: float = Field(
        default=0.5,
        description="Tolerance for simplifying extracted contours",
    )
    max_segments: int = Field(
        default=100,
        description="Maximum number of segments for contour extraction",
    )
    min_area_fraction: float = Field(
        default=0.01,
        description="Minimum area fraction for contour extraction",
    )


class TriangulationConfig(BaseModel):

    triangulator_add_interior_points: bool = Field(
        default=True, description="Whether to add interior points during triangulation"
    )
    triangulator_interior_point_density: float = Field(
        default=1.0, description="Density of interior points (points per unit area)"
    )


class PostProcessingConfig(BaseModel):
    apply_post_processing: bool = Field(
        default=True, description="Whether to apply post-processing to meshes"
    )
    remove_degenerate_triangles: bool = Field(
        default=True, description="Remove degenerate triangles"
    )
    remove_duplicated_vertices: bool = Field(
        default=True, description="Remove duplicated vertices"
    )
    remove_duplicated_triangles: bool = Field(
        default=True, description="Remove duplicated triangles"
    )
    remove_unreferenced_vertices: bool = Field(
        default=True, description="Remove unreferenced vertices"
    )
    merge_close_vertices: bool = Field(
        default=False, description="Merge vertices that are very close"
    )
    merge_vertices_threshold: float = Field(
        default=1e-6, description="Distance threshold for merging vertices"
    )
    simplification_method: str = Field(
        default="none", description="Method for mesh simplification"
    )
    target_triangle_count: int = Field(
        default=100000, description="Target triangle count for mesh simplification"
    )
    voxel_size: float = Field(
        default=0.05, description="Voxel size for vertex clustering simplification"
    )


class MeshGenerationConfig(BaseModel):

    stateless: bool = Field(
        default=True, description="Whether to run in stateless mode (no visualizations)"
    )

    heightmap_processing: HeighmapProcessingConfig = Field(
        default_factory=HeighmapProcessingConfig,
    )
    mesh_combination: MeshCombinationConfig = Field(
        default_factory=MeshCombinationConfig,
    )
    contour_extraction: ContourExtractionConfig = Field(
        default_factory=ContourExtractionConfig,
    )
    triangulation: TriangulationConfig = Field(
        default_factory=TriangulationConfig,
    )
    post_processing: PostProcessingConfig = Field(
        default_factory=PostProcessingConfig,
    )


class ImageProcessingConfig(BaseModel):

    preserve_full_resolution: bool = Field(
        default=True, description="Whether to preserve full image resolution"
    )

    max_dimension: Optional[int] = Field(
        default=None, description="Maximum dimension (width/height) for resizing images"
    )

    region: Optional[tuple[int, int, int, int]] = Field(
        default=None,
        description="Region of interest in the format (left, upper, right, lower)",
    )

    fill_nan_values: bool = Field(
        default=True, description="Whether to fill NaN values in images"
    )

    fill_max_iterations: int = Field(
        default=100, description="Maximum iterations for filling NaN values"
    )
    fill_neighborhood: int = Field(
        default=1, description="Neighborhood size for filling NaN values"
    )

    color_map: OrderedDict = Field(
        default_factory=lambda: OrderedDict(
            {
                "#0000FF": {"value": -10.0, "fuzziness": 5.0},  # Deep water
                "#00FFFF": {"value": -5.0, "fuzziness": 5.0},  # Shallow water
                "#00FF00": {"value": 0.0, "fuzziness": 5.0},  # Shoreline
                "#FFFF00": {"value": 5.0, "fuzziness": 5.0},  # Low land
                "#FF0000": {"value": 10.0, "fuzziness": 5.0},  # High land
            }
        ),
        description="Color to value mapping with fuzziness",
    )
    default_fuzziness: float = Field(
        default=10.0, description="Default fuzziness value (Delta E) when not specified"
    )


class ProjectConfig(BaseModel):

    mesh_generation: MeshGenerationConfig = Field(
        default_factory=MeshGenerationConfig,
    )

    image_processing: ImageProcessingConfig = Field(
        default_factory=ImageProcessingConfig,
    )
