"""Reusable configuration table widget for editing config dataclasses."""

import logging
from dataclasses import fields
from typing import Any, Union

from textual.coordinate import Coordinate
from textual.widgets import DataTable

from bathy.config import (
    ContourExtractionConfig,
    HeighmapProcessingConfig,
    ImageProcessingConfig,
    MeshCombinationConfig,
    MeshGenerationConfig,
    PostProcessingConfig,
    TriangulationConfig,
)

logger = logging.getLogger(__name__)


class ConfigTable(DataTable):
    """DataTable widget for editing configuration parameters.

    Displays config parameters with section headers. Values are editable.
    Supports both ImageProcessingConfig and MeshGenerationConfig.

    Press Enter on a value cell to edit it.
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize ConfigTable."""
        super().__init__(**kwargs)
        self.cursor_type = "cell"  # Changed to cell for editing
        self._config_type: Union[str, None] = None
        self._editing_cell: Union[Coordinate, None] = None

    def load_config(
        self, config: Union[ImageProcessingConfig, MeshGenerationConfig]
    ) -> None:
        """Load configuration into table.

        Args:
            config: Configuration object to display
        """
        self.clear()
        self.add_columns("Parameter", "Value")

        # Determine config type
        if isinstance(config, ImageProcessingConfig):
            self._config_type = "image"
            self._load_image_config(config)
        elif isinstance(config, MeshGenerationConfig):
            self._config_type = "mesh"
            self._load_mesh_config(config)

    def _load_image_config(self, config: ImageProcessingConfig) -> None:
        """Load image processing configuration."""
        # Basic settings
        self._add_header("Basic Settings")
        self._add_param("preserve_full_resolution", config.preserve_full_resolution)
        self._add_param("max_dimension", config.max_dimension)

        # Region of Interest
        self._add_header("Region of Interest")
        self._add_param("region", config.region)

        # NaN Filling
        self._add_header("NaN Value Filling")
        self._add_param("fill_nan_values", config.fill_nan_values)
        self._add_param("fill_max_iterations", config.fill_max_iterations)
        self._add_param("fill_neighborhood", config.fill_neighborhood)

        # Color Map (simplified - just show it exists)
        self._add_header("Color Map")
        self._add_param("default_fuzziness", config.default_fuzziness)
        self.add_row("color_map", f"{len(config.color_map)} entries")

    def _load_mesh_config(self, config: MeshGenerationConfig) -> None:
        """Load mesh generation configuration."""
        # Basic
        self._add_header("Basic Settings")
        self._add_param("stateless", config.stateless)

        # Heightmap Processing
        self._add_header("Heightmap Processing")
        hp = config.heightmap_processing
        self._add_param("exterior_buffer_width", hp.exterior_buffer_width)
        self._add_param("exterior_buffer_value", hp.exterior_buffer_value)
        self._add_param("data_offset", hp.data_offset)
        self._add_param("base_height", hp.base_height)
        self._add_param("layer_thickness", hp.layer_thickness)
        self.add_row("thresholds", f"{len(hp.thresholds)} values")

        # Units
        self._add_header("Mesh Units")
        self._add_param("units_x", hp.mesh_units.units_x)
        self._add_param("units_y", hp.mesh_units.units_y)
        self._add_param("units_z", hp.mesh_units.units_z)

        # Contour Extraction
        self._add_header("Contour Extraction")
        ce = config.contour_extraction
        self._add_param("min_polygon_area", ce.min_polygon_area)
        self._add_param("simplify_tolerance", ce.simplify_tolerance)
        self._add_param("max_segments", ce.max_segments)
        self._add_param("min_area_fraction", ce.min_area_fraction)

        # Triangulation
        self._add_header("Triangulation")
        tri = config.triangulation
        self._add_param(
            "triangulator_add_interior_points", tri.triangulator_add_interior_points
        )
        self._add_param(
            "triangulator_interior_point_density",
            tri.triangulator_interior_point_density,
        )

        # Mesh Combination
        self._add_header("Mesh Combination")
        self._add_param("merge_threshold", config.mesh_combination.merge_threshold)

        # Post Processing
        self._add_header("Post Processing")
        pp = config.post_processing
        self._add_param("apply_post_processing", pp.apply_post_processing)
        self._add_param("remove_degenerate_triangles", pp.remove_degenerate_triangles)
        self._add_param("remove_duplicated_vertices", pp.remove_duplicated_vertices)
        self._add_param("remove_duplicated_triangles", pp.remove_duplicated_triangles)
        self._add_param("remove_unreferenced_vertices", pp.remove_unreferenced_vertices)
        self._add_param("merge_close_vertices", pp.merge_close_vertices)
        self._add_param("merge_vertices_threshold", pp.merge_vertices_threshold)
        self._add_param("simplification_method", pp.simplification_method)
        self._add_param("target_triangle_count", pp.target_triangle_count)
        self._add_param("voxel_size", pp.voxel_size)

    def _add_header(self, title: str) -> None:
        """Add a section header row (not editable)."""
        self.add_row(f"[bold]▶ {title}[/]", "", key=f"header_{title}")

    def _add_param(self, name: str, value: Any) -> None:
        """Add a parameter row (value column is editable)."""
        value_str = str(value) if value is not None else "None"
        self.add_row(name, value_str, key=f"param_{name}")

    def update_param_value(self, param_name: str, new_value: str) -> None:
        """Update a parameter's value in the table.

        Args:
            param_name: Name of the parameter
            new_value: New value as string
        """
        row_key = f"param_{param_name}"
        if row_key in self.rows:
            row_index = list(self.rows.keys()).index(row_key)
            # Update the value column (column 1)
            logger.info(row_key)
            logger.info([x.value for x in self.columns])
            self.update_cell(
                row_key, list(self.columns.keys())[1], new_value, update_width=True
            )
            logger.debug(f"Updated {param_name} = {new_value}")

    def on_key(self, event) -> None:
        """Handle key presses for editing."""
        # Enter key starts editing the value column
        if event.key == "enter" and self.cursor_coordinate:
            row, col = self.cursor_coordinate

            # Only allow editing value column (column 1) and not header rows
            row_key = self.coordinate_to_cell_key(self.cursor_coordinate).row_key
            row_key_str = row_key.value if row_key.value is not None else ""

            if col == 1 and row_key_str.startswith("param_"):
                param_name = row_key_str.replace("param_", "")
                current_value = self.get_cell_at(self.cursor_coordinate)

                # Show input dialog for editing
                self._start_editing(param_name, str(current_value))
                event.prevent_default()

    def _start_editing(self, param_name: str, current_value: str) -> None:
        """Start editing a parameter value.

        Args:
            param_name: Name of the parameter being edited
            current_value: Current value as string
        """
        from bathy.ui.widgets.edit_value_dialog import EditValueDialog

        # Get description from config metadata if available
        description = self._get_param_description(param_name)

        def handle_edit(new_value: Union[str, None]) -> None:
            if new_value is not None:
                # Validate and update
                try:
                    parsed = self._parse_value(new_value)
                    self.update_param_value(param_name, new_value)
                    logger.info(f"Updated {param_name} to {new_value}")
                except Exception as e:
                    logger.error(f"Invalid value for {param_name}: {e}")
                    # Could show error notification here

        self.app.push_screen(
            EditValueDialog(param_name, current_value, description), handle_edit
        )

    def get_config_dict(self) -> dict[str, Any]:
        """Extract configuration values from table as dictionary.

        Returns:
            Dictionary of parameter names to values
        """
        config_dict = {}

        for row_key in self.rows:
            if isinstance(row_key, str) and row_key.startswith("param_"):
                param_name = row_key.replace("param_", "")
                row = self.get_row(row_key)
                value_str = str(row[1])

                # Parse value string back to appropriate type
                config_dict[param_name] = self._parse_value(value_str)

        return config_dict

    def _parse_value(self, value_str: str) -> Any:
        """Parse string value back to appropriate Python type.

        Args:
            value_str: String representation of value

        Returns:
            Parsed value (bool, int, float, None, or str)
        """
        value_str = value_str.strip()

        # Handle None
        if value_str == "None":
            return None

        # Handle booleans
        if value_str == "True":
            return True
        if value_str == "False":
            return False

        # Try int
        try:
            return int(value_str)
        except ValueError:
            pass

        # Try float
        try:
            return float(value_str)
        except ValueError:
            pass

        # Return as string
        return value_str

    def _get_param_description(self, param_name: str) -> Union[str, None]:
        """Get parameter description from config dataclass metadata.

        Args:
            param_name: Name of the parameter

        Returns:
            Description string or None if not found
        """
        # Map of config classes to search for the parameter
        config_classes = [
            ImageProcessingConfig,
            MeshGenerationConfig,
            HeighmapProcessingConfig,
            ContourExtractionConfig,
            TriangulationConfig,
            MeshCombinationConfig,
            PostProcessingConfig,
        ]

        for config_class in config_classes:
            for field in fields(config_class):
                if field.name == param_name:
                    # Get description from metadata
                    if "help" in field.metadata:
                        return field.metadata["help"]
                    return None

        return None
