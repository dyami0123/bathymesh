"""Mesh workflow widget for generating 3D meshes from heightmaps."""

import logging
from pathlib import Path
from typing import Union

import numpy as np
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Static
from textual.worker import get_current_worker

from bathy.config import (
    ContourExtractionConfig,
    HeighmapProcessingConfig,
    MeshCombinationConfig,
    MeshGenerationConfig,
    MeshUnits,
    PostProcessingConfig,
    TriangulationConfig,
)
from bathy.project_manager import Project
from bathy.ui.widgets.config_table import ConfigTable
from bathy.ui.widgets.processing_modal import ProcessingModal
from bathy.workflows.generate_mesh import generate_mesh

logger = logging.getLogger(__name__)


class MeshWorkflowWidget(Vertical):
    """Heightmap → Mesh workflow tab.

    Allows user to select a heightmap, configure mesh generation parameters,
    preview file info, and process the heightmap to generate a 3D mesh.
    """

    def __init__(self, project: Project, **kwargs) -> None:
        """Initialize MeshWorkflowWidget.

        Args:
            project: Project instance
            **kwargs: Additional arguments for Vertical
        """
        super().__init__(**kwargs)
        self._project = project
        self._file_info_loaded = False

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        # File selection section
        with Container(classes="section"):
            yield Label("Heightmap Selection", classes="section-heading")
            yield Input(placeholder="/path/to/heightmap.npy", id="file-input")
            yield Button("📊 Use Project Heightmap", id="use-heightmap-button")

        # File info section (initially empty)
        with Container(id="file-info-container") as info_container:
            info_container.display = False
            yield Label(
                "File Information", classes="section-heading", id="file-info-label"
            )
            yield Static("", id="file-info-text")

        # Configuration section
        with Container(classes="section"):
            yield Label("Mesh Generation Configuration", classes="section-heading")
            config_table = ConfigTable(id="config-table")
            yield config_table

        # Button bar
        with Horizontal(classes="button-bar"):
            yield Button(
                "🔍 Preview File",
                id="preview-button",
                variant="default",
                classes="action-button",
            )
            yield Button(
                "▶️ Process",
                id="process-button",
                variant="primary",
                classes="action-button",
            )

        # Status log
        yield RichLog(id="status-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        """Initialize widget after mounting."""
        # Load existing config or create default
        try:
            config = self._project.load_mesh_config()
            logger.debug("Loaded existing mesh config")
        except Exception as e:
            logger.warning(f"Could not load config, using defaults: {e}")
            config = MeshGenerationConfig()

        # Populate config table
        config_table = self.query_one("#config-table", ConfigTable)
        config_table.load_config(config)

        # Pre-fill heightmap if available
        heightmap_path = self._project.get_heightmap()
        if heightmap_path:
            file_input = self.query_one("#file-input", Input)
            file_input.value = str(heightmap_path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "use-heightmap-button":
            self._use_project_heightmap()
        elif event.button.id == "preview-button":
            self._preview_file()
        elif event.button.id == "process-button":
            self._start_processing()

    def _use_project_heightmap(self) -> None:
        """Fill input with project heightmap path."""
        heightmap_path = self._project.get_heightmap()
        if heightmap_path:
            file_input = self.query_one("#file-input", Input)
            file_input.value = str(heightmap_path)

            status_log = self.query_one("#status-log", RichLog)
            status_log.write(
                f"[green]Set path to project heightmap: {heightmap_path}[/]"
            )
        else:
            status_log = self.query_one("#status-log", RichLog)
            status_log.write("[yellow]No heightmap generated in project yet[/]")

    def _preview_file(self) -> None:
        """Preview file and load info."""
        file_input = self.query_one("#file-input", Input)
        file_path_str = file_input.value.strip()

        if not file_path_str:
            status_log = self.query_one("#status-log", RichLog)
            status_log.write("[red]Please enter a file path[/]")
            return

        file_path = Path(file_path_str)
        if not file_path.exists():
            status_log = self.query_one("#status-log", RichLog)
            status_log.write(f"[red]File not found: {file_path}[/]")
            return

        # Load file info in worker
        self._load_file_info(file_path)

    @work(exclusive=True, thread=True)
    def _load_file_info(self, file_path: Path) -> None:
        """Load heightmap information in worker thread.

        Args:
            file_path: Path to heightmap file
        """
        worker = get_current_worker()
        status_log = self.query_one("#status-log", RichLog)

        try:
            self.app.call_from_thread(status_log.write, "Loading file info...")

            # Load heightmap (blocking operation)
            data = np.load(file_path)
            size_mb = file_path.stat().st_size / (1024 * 1024)

            info_text = f"""Shape: {data.shape}
Data Type: {data.dtype}
Min Value: {np.nanmin(data):.3f}
Max Value: {np.nanmax(data):.3f}
Mean Value: {np.nanmean(data):.3f}
NaN Count: {np.count_nonzero(np.isnan(data))}
File Size: {size_mb:.2f} MB"""

            # Update UI
            if not worker.is_cancelled:

                def update_ui():
                    file_info_container = self.query_one(
                        "#file-info-container", Container
                    )
                    file_info_container.display = True

                    file_info_text = self.query_one("#file-info-text", Static)
                    file_info_text.update(info_text)

                    status_log.write("[green]File info loaded successfully[/]")

                self.app.call_from_thread(update_ui)
                self._file_info_loaded = True
                logger.info(f"Loaded file info: {file_path.name}")

        except Exception as e:
            if not worker.is_cancelled:
                error_msg = f"[red]Error loading file: {e}[/]"
                self.app.call_from_thread(status_log.write, error_msg)
                logger.error(f"Failed to load file info: {e}")

    def _start_processing(self) -> None:
        """Start processing workflow."""
        # Validate file path
        file_input = self.query_one("#file-input", Input)
        file_path_str = file_input.value.strip()

        if not file_path_str:
            status_log = self.query_one("#status-log", RichLog)
            status_log.write("[red]Please enter a file path[/]")
            return

        file_path = Path(file_path_str)
        if not file_path.exists():
            status_log = self.query_one("#status-log", RichLog)
            status_log.write(f"[red]File not found: {file_path}[/]")
            return

        # Build config from table
        config_table = self.query_one("#config-table", ConfigTable)
        config_dict = config_table.get_config_dict()

        # Reconstruct MeshGenerationConfig with nested structures
        config = self._reconstruct_mesh_config(config_dict)

        # Save config to project
        try:
            self._project.save_mesh_config(config)
            logger.debug("Saved mesh config to project")
        except Exception as e:
            logger.warning(f"Could not save config: {e}")

        # Show processing modal
        modal = ProcessingModal(title="Processing Heightmap → Mesh")
        self.app.push_screen(modal)

        # Start processing in worker
        self._run_processing(file_path, config, modal)

    def _reconstruct_mesh_config(self, config_dict: dict) -> MeshGenerationConfig:
        """Reconstruct MeshGenerationConfig from flat config dictionary.

        Args:
            config_dict: Flat dictionary from ConfigTable

        Returns:
            Properly structured MeshGenerationConfig
        """
        # Load existing config to get thresholds (not editable in table yet)
        try:
            existing_config = self._project.load_mesh_config()
            thresholds = existing_config.heightmap_processing.thresholds
        except Exception:
            # Use defaults if can't load
            thresholds = HeighmapProcessingConfig().thresholds

        # Reconstruct nested configs
        mesh_units = MeshUnits(
            units_x=config_dict.get("units_x", 1.0),
            units_y=config_dict.get("units_y", 1.0),
            units_z=config_dict.get("units_z", 1.0),
        )

        heightmap_processing = HeighmapProcessingConfig(
            exterior_buffer_width=config_dict.get("exterior_buffer_width", 0),
            exterior_buffer_value=config_dict.get("exterior_buffer_value", 0.0),
            data_offset=config_dict.get("data_offset", 0.0),
            mesh_units=mesh_units,
            thresholds=thresholds,
            base_height=config_dict.get("base_height", 0.0),
            layer_thickness=config_dict.get("layer_thickness", 0.5),
        )

        mesh_combination = MeshCombinationConfig(
            merge_threshold=config_dict.get("merge_threshold", 1e-6),
        )

        contour_extraction = ContourExtractionConfig(
            min_polygon_area=config_dict.get("min_polygon_area", 1e-2),
            simplify_tolerance=config_dict.get("simplify_tolerance", 0.5),
            max_segments=config_dict.get("max_segments", 100),
            min_area_fraction=config_dict.get("min_area_fraction", 0.01),
        )

        triangulation = TriangulationConfig(
            triangulator_add_interior_points=config_dict.get(
                "triangulator_add_interior_points", True
            ),
            triangulator_interior_point_density=config_dict.get(
                "triangulator_interior_point_density", 1.0
            ),
        )

        post_processing = PostProcessingConfig(
            apply_post_processing=config_dict.get("apply_post_processing", True),
            remove_degenerate_triangles=config_dict.get(
                "remove_degenerate_triangles", True
            ),
            remove_duplicated_vertices=config_dict.get(
                "remove_duplicated_vertices", True
            ),
            remove_duplicated_triangles=config_dict.get(
                "remove_duplicated_triangles", True
            ),
            remove_unreferenced_vertices=config_dict.get(
                "remove_unreferenced_vertices", True
            ),
            merge_close_vertices=config_dict.get("merge_close_vertices", False),
            merge_vertices_threshold=config_dict.get("merge_vertices_threshold", 1e-6),
            simplification_method=config_dict.get("simplification_method", "none"),
            target_triangle_count=config_dict.get("target_triangle_count", 100000),
            voxel_size=config_dict.get("voxel_size", 0.05),
        )

        return MeshGenerationConfig(
            stateless=config_dict.get("stateless", True),
            heightmap_processing=heightmap_processing,
            mesh_combination=mesh_combination,
            contour_extraction=contour_extraction,
            triangulation=triangulation,
            post_processing=post_processing,
        )

    @work(exclusive=True, thread=True)
    def _run_processing(
        self, file_path: Path, config: MeshGenerationConfig, modal: ProcessingModal
    ) -> None:
        """Run mesh generation workflow in worker thread.

        Args:
            file_path: Path to heightmap file
            config: Mesh generation configuration
            modal: Modal to update with progress
        """
        worker = get_current_worker()

        try:
            # Log start
            self.app.call_from_thread(modal.append_log, "Starting mesh generation...")
            self.app.call_from_thread(modal.append_log, f"Heightmap: {file_path}")
            self.app.call_from_thread(modal.append_log, "")

            if worker.is_cancelled:
                return

            # Determine output path
            meshes_dir = self._project.meshes_dir
            meshes_dir.mkdir(exist_ok=True)
            output_path = meshes_dir / f"{file_path.stem}_mesh.stl"

            self.app.call_from_thread(modal.append_log, f"Output: {output_path}")
            self.app.call_from_thread(modal.append_log, "")

            if worker.is_cancelled:
                return

            # Run workflow (blocking operation)
            self.app.call_from_thread(modal.append_log, "Loading heightmap...")
            mesh_data, generator = generate_mesh(
                file_path, config, save_path=output_path
            )

            if worker.is_cancelled:
                return

            self.app.call_from_thread(
                modal.append_log,
                f"Generated mesh with {len(mesh_data.data.triangles)} triangles",
            )
            self.app.call_from_thread(modal.append_log, f"Saved to: {output_path}")

            # Update project metadata
            self._project.set_latest_mesh(output_path)

            self.app.call_from_thread(modal.append_log, "")
            self.app.call_from_thread(
                modal.mark_complete, True, "✓ Mesh generation complete!"
            )

            # Update status log
            status_log = self.query_one("#status-log", RichLog)
            self.app.call_from_thread(
                status_log.write,
                f"[bold green]✓ Successfully generated mesh: {output_path.name}[/]",
            )

            logger.info(f"Mesh generation complete: {output_path}")

        except Exception as e:
            if not worker.is_cancelled:
                error_msg = f"✗ Processing failed: {e}"
                self.app.call_from_thread(modal.mark_complete, False, error_msg)

                status_log = self.query_one("#status-log", RichLog)
                self.app.call_from_thread(status_log.write, f"[bold red]{error_msg}[/]")

                logger.error(f"Mesh generation failed: {e}", exc_info=True)
