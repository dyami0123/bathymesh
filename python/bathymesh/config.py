"""Configuration management for bathymesh."""

import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Optional, Union

import yaml

from bathymesh.mesh_post_processor import SimplificationMethod

logger = logging.getLogger(__name__)


@dataclass
class ContourParams:
    """Parameters for contour extraction."""
    min_polygon_area: float = 1e-2
    simplify_tolerance: float = 0.5
    max_segments: int = 100
    min_area_fraction: float = 0.01


@dataclass
class CombinerParams:
    """Parameters for mesh combination."""
    merge_threshold: float = 1e-6


@dataclass
class TriangulationParams:
    """Parameters for triangulation."""
    add_interior_points: bool = True
    interior_point_density: float = 1.0


@dataclass
class PostProcessParams:
    """Parameters for mesh post-processing."""
    enabled: bool = True
    # Basic cleanup
    remove_degenerate_triangles: bool = True
    remove_duplicated_vertices: bool = True
    remove_duplicated_triangles: bool = True
    remove_unreferenced_vertices: bool = True
    # Vertex merging
    merge_close_vertices: bool = False
    merge_vertices_threshold: float = 1e-6
    # Simplification
    simplification_method: SimplificationMethod = SimplificationMethod.NONE
    target_triangle_count: int = 100000
    voxel_size: float = 0.05


@dataclass
class GenerationParams:
    """Core parameters for mesh generation."""
    thresholds: List[float] = field(default_factory=list)
    base_height: float = 0.0
    layer_thickness: float = 1.0


@dataclass
class MeshConfig:
    """Master configuration for mesh generation."""
    generation: GenerationParams = field(default_factory=GenerationParams)
    contour: ContourParams = field(default_factory=ContourParams)
    combiner: CombinerParams = field(default_factory=CombinerParams)
    triangulation: TriangulationParams = field(default_factory=TriangulationParams)
    post_process: PostProcessParams = field(default_factory=PostProcessParams)

    @classmethod
    def load_from_yaml(cls, path: Union[str, Path]) -> "MeshConfig":
        """Load configuration from a YAML file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            data = yaml.safe_load(f)

        # Helper to recursively load nested dataclasses
        # Note: This is a simple implementation. For more complex cases, 
        # libraries like dacite or pydantic are recommended.
        # Here we assume the YAML structure matches the dataclass structure.
        
        try:
            gen_data = data.get("generation", {})
            contour_data = data.get("contour", {})
            combiner_data = data.get("combiner", {})
            tri_data = data.get("triangulation", {})
            pp_data = data.get("post_process", {})

            # Handle enum conversion for simplification method
            if "simplification_method" in pp_data:
                method_str = pp_data["simplification_method"]
                if isinstance(method_str, str):
                    # Remove 'SimplificationMethod.' prefix if present
                    if "." in method_str:
                        method_str = method_str.split(".")[-1]
                    pp_data["simplification_method"] = SimplificationMethod[method_str]

            return cls(
                generation=GenerationParams(**gen_data),
                contour=ContourParams(**contour_data),
                combiner=CombinerParams(**combiner_data),
                triangulation=TriangulationParams(**tri_data),
                post_process=PostProcessParams(**pp_data),
            )
        except Exception as e:
            raise ValueError(f"Failed to parse config from {path}: {e}") from e

    def save_to_yaml(self, path: Union[str, Path]) -> None:
        """Save configuration to a YAML file."""
        path = Path(path)
        
        data = asdict(self)
        
        # Handle enum serialization
        pp_data = data["post_process"]
        if "simplification_method" in pp_data:
            pp_data["simplification_method"] = self.post_process.simplification_method.name

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)
