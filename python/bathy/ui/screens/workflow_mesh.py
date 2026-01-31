"""Heightmap to Mesh workflow screen."""

import logging
from pathlib import Path

import numpy as np
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    Collapsible,
    Input,
    Label,
    LoadingIndicator,
    RichLog,
    Static,
)

from bathy.config import (
    ContourExtractionConfig,
    HeighmapProcessingConfig,
    MeshCombinationConfig,
    MeshGenerationConfig,
    MeshUnits,
    PostProcessingConfig,
    TriangulationConfig,
)
from bathy.workflows.generate_mesh import generate_mesh

logger = logging.getLogger(__name__)


class WorkflowMeshScreen(Screen):
    """Screen for Heightmap → Mesh workflow."""

    def __init__(self, **kwargs):
        """Initialize the workflow screen."""
        super().__init__(**kwargs)
        self.processing = False

    CSS = """
    WorkflowMeshScreen {
        align: left top;
        padding: 1 2;
    }
    
    #workflow-container {
        width: 100%;
        height: 100%;
        background: $surface;
    }
    
    #workflow-header {
        width: 100%;
        height: auto;
        background: $panel;
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    #workflow-title {
        width: 100%;
        text-align: left;
        color: $accent;
        text-style: bold;
    }
    
    #content-area {
        width: 100%;
        height: 1fr;
    }
    
    #config-scroll {
        width: 100%;
        height: 1fr;
        border: solid $primary;
        padding: 1;
    }
    
    Collapsible {
        width: 100%;
        margin: 1 0;
    }
    
    .field {
        width: 100%;
        height: auto;
        margin: 1 0;
    }
    
    .field-label {
        width: 100%;
        color: $text;
        margin-bottom: 1;
    }
    
    Input {
        width: 100%;
    }
    
    Checkbox {
        width: 100%;
        margin: 1 0;
    }
    
    #status-area {
        width: 100%;
        height: 10;
        border: solid $primary;
        padding: 0;
        background: $panel;
        margin-top: 1;
    }
    
    #status-log {
        width: 100%;
        height: 1fr;
        border: none;
    }
    
    LoadingIndicator {
        height: 3;
        width: 100%;
        background: $panel;
    }
    
    #button-bar {
        width: 100%;
        height: auto;
        align: right middle;
        margin-top: 1;
    }
    
    #button-bar Button {
        margin: 0 1;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the workflow screen."""
        with Vertical(id="workflow-container"):
            # Header
            with Container(id="workflow-header"):
                yield Static("🗻  Heightmap → Mesh Workflow", id="workflow-title")

            # Content area
            with Container(id="content-area"):
                # Scrollable config area
                with ScrollableContainer(id="config-scroll"):
                    # Heightmap info
                    yield Static("Heightmap Source", classes="field-label")
                    yield Static("", id="heightmap-info")

                    # Heightmap Processing Config
                    with Collapsible(title="🔧 Heightmap Processing", collapsed=False):
                        with Container(classes="field"):
                            yield Label("Exterior Buffer Width:", classes="field-label")
                            yield Input(value="0", id="buffer-width-input")

                        with Container(classes="field"):
                            yield Label("Exterior Buffer Value:", classes="field-label")
                            yield Input(value="0.0", id="buffer-value-input")

                        with Container(classes="field"):
                            yield Label("Data Offset:", classes="field-label")
                            yield Input(value="0.0", id="data-offset-input")

                        with Container(classes="field"):
                            yield Label("Mesh Units X:", classes="field-label")
                            yield Input(value="1.0", id="units-x-input")

                        with Container(classes="field"):
                            yield Label("Mesh Units Y:", classes="field-label")
                            yield Input(value="1.0", id="units-y-input")

                        with Container(classes="field"):
                            yield Label("Mesh Units Z:", classes="field-label")
                            yield Input(value="1.0", id="units-z-input")

                        with Container(classes="field"):
                            yield Label("Base Height:", classes="field-label")
                            yield Input(value="0.0", id="base-height-input")

                        with Container(classes="field"):
                            yield Label("Layer Thickness:", classes="field-label")
                            yield Input(value="0.5", id="layer-thickness-input")

                        with Container(classes="field"):
                            yield Label("Thresholds (linspace):", classes="field-label")
                            yield Label("  Start:", classes="field-label")
                            yield Input(value="0", id="threshold-start-input")
                            yield Label("  End:", classes="field-label")
                            yield Input(value="50", id="threshold-end-input")
                            yield Label("  Count:", classes="field-label")
                            yield Input(value="10", id="threshold-count-input")

                    # Contour Extraction Config
                    with Collapsible(title="📐 Contour Extraction", collapsed=True):
                        with Container(classes="field"):
                            yield Label("Min Polygon Area:", classes="field-label")
                            yield Input(value="0.01", id="min-polygon-area-input")

                        with Container(classes="field"):
                            yield Label("Simplify Tolerance:", classes="field-label")
                            yield Input(value="0.5", id="simplify-tolerance-input")

                        with Container(classes="field"):
                            yield Label("Max Segments:", classes="field-label")
                            yield Input(value="100", id="max-segments-input")

                        with Container(classes="field"):
                            yield Label("Min Area Fraction:", classes="field-label")
                            yield Input(value="0.01", id="min-area-fraction-input")

                    # Triangulation Config
                    with Collapsible(title="🔺 Triangulation", collapsed=True):
                        yield Checkbox(
                            "Add Interior Points",
                            id="add-interior-points-checkbox",
                            value=True,
                        )

                        with Container(classes="field"):
                            yield Label(
                                "Interior Point Density:", classes="field-label"
                            )
                            yield Input(value="1.0", id="interior-point-density-input")

                    # Post Processing Config
                    with Collapsible(title="✨ Post Processing", collapsed=True):
                        yield Checkbox(
                            "Apply Post Processing",
                            id="apply-post-processing-checkbox",
                            value=True,
                        )
                        yield Checkbox(
                            "Remove Degenerate Triangles",
                            id="remove-degenerate-checkbox",
                            value=True,
                        )
                        yield Checkbox(
                            "Remove Duplicated Vertices",
                            id="remove-dup-vertices-checkbox",
                            value=True,
                        )
                        yield Checkbox(
                            "Remove Duplicated Triangles",
                            id="remove-dup-triangles-checkbox",
                            value=True,
                        )
                        yield Checkbox(
                            "Remove Unreferenced Vertices",
                            id="remove-unref-vertices-checkbox",
                            value=True,
                        )
                        yield Checkbox(
                            "Merge Close Vertices",
                            id="merge-close-vertices-checkbox",
                            value=False,
                        )

                        with Container(classes="field"):
                            yield Label(
                                "Merge Vertices Threshold:", classes="field-label"
                            )
                            yield Input(value="1e-6", id="merge-threshold-input")

                    # Mesh Combination Config
                    with Collapsible(title="🔗 Mesh Combination", collapsed=True):
                        with Container(classes="field"):
                            yield Label("Merge Threshold:", classes="field-label")
                            yield Input(value="1e-6", id="mesh-merge-threshold-input")

            # Status area
            with Container(id="status-area"):
                yield LoadingIndicator(id="loading-indicator")
                yield RichLog(id="status-log", highlight=True, markup=True)

            # Button bar
            with Horizontal(id="button-bar"):
                yield Button("Generate Mesh", id="generate-btn", variant="success")
                yield Button("Back", id="back-btn", variant="default")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Hide loading indicator initially
        self.query_one("#loading-indicator", LoadingIndicator).display = False

        # Log initial message
        self._log("[bold green]Ready to generate mesh[/bold green]")

        # Load existing config if available
        project = self.app.current_project
        if project:
            self._display_heightmap_info()
            self._load_existing_config()

    def _display_heightmap_info(self) -> None:
        """Display information about the current heightmap."""
        project = self.app.current_project
        if not project:
            return

        heightmap_info = self.query_one("#heightmap-info", Static)

        if project.metadata.heightmap_file:
            heightmap_path = project.get_heightmap()
            if heightmap_path and heightmap_path.exists():
                # Load heightmap to get info
                try:
                    data = np.load(heightmap_path)
                    size_mb = heightmap_path.stat().st_size / (1024 * 1024)
                    info_text = f"{heightmap_path.name} ({size_mb:.2f} MB)\n"
                    info_text += f"Shape: {data.shape}, Min: {np.nanmin(data):.2f}, Max: {np.nanmax(data):.2f}"
                    heightmap_info.update(info_text)
                except Exception as e:
                    heightmap_info.update(f"Error loading heightmap: {e}")
            else:
                heightmap_info.update("Heightmap file not found")
        else:
            heightmap_info.update(
                "No heightmap available. Run Image→Heightmap workflow first."
            )

    def _load_existing_config(self) -> None:
        """Load existing mesh config from project if available."""
        project = self.app.current_project
        if not project:
            return

        try:
            config = project.load_mesh_config()

            # Load heightmap processing config
            hp = config.heightmap_processing
            self.query_one("#buffer-width-input", Input).value = str(
                hp.exterior_buffer_width
            )
            self.query_one("#buffer-value-input", Input).value = str(
                hp.exterior_buffer_value
            )
            self.query_one("#data-offset-input", Input).value = str(hp.data_offset)
            self.query_one("#units-x-input", Input).value = str(hp.mesh_units.units_x)
            self.query_one("#units-y-input", Input).value = str(hp.mesh_units.units_y)
            self.query_one("#units-z-input", Input).value = str(hp.mesh_units.units_z)
            self.query_one("#base-height-input", Input).value = str(hp.base_height)
            self.query_one("#layer-thickness-input", Input).value = str(
                hp.layer_thickness
            )

            # For thresholds, show the linspace parameters if it looks like a linspace
            if len(hp.thresholds) > 1:
                self.query_one("#threshold-start-input", Input).value = str(
                    hp.thresholds[0]
                )
                self.query_one("#threshold-end-input", Input).value = str(
                    hp.thresholds[-1]
                )
                self.query_one("#threshold-count-input", Input).value = str(
                    len(hp.thresholds)
                )

            # Load contour extraction config
            ce = config.contour_extraction
            self.query_one("#min-polygon-area-input", Input).value = str(
                ce.min_polygon_area
            )
            self.query_one("#simplify-tolerance-input", Input).value = str(
                ce.simplify_tolerance
            )
            self.query_one("#max-segments-input", Input).value = str(ce.max_segments)
            self.query_one("#min-area-fraction-input", Input).value = str(
                ce.min_area_fraction
            )

            # Load triangulation config
            tri = config.triangulation
            self.query_one(
                "#add-interior-points-checkbox", Checkbox
            ).value = tri.triangulator_add_interior_points
            self.query_one("#interior-point-density-input", Input).value = str(
                tri.triangulator_interior_point_density
            )

            # Load post processing config
            pp = config.post_processing
            self.query_one(
                "#apply-post-processing-checkbox", Checkbox
            ).value = pp.apply_post_processing
            self.query_one(
                "#remove-degenerate-checkbox", Checkbox
            ).value = pp.remove_degenerate_triangles
            self.query_one(
                "#remove-dup-vertices-checkbox", Checkbox
            ).value = pp.remove_duplicated_vertices
            self.query_one(
                "#remove-dup-triangles-checkbox", Checkbox
            ).value = pp.remove_duplicated_triangles
            self.query_one(
                "#remove-unref-vertices-checkbox", Checkbox
            ).value = pp.remove_unreferenced_vertices
            self.query_one(
                "#merge-close-vertices-checkbox", Checkbox
            ).value = pp.merge_close_vertices
            self.query_one("#merge-threshold-input", Input).value = str(
                pp.merge_vertices_threshold
            )

            # Load mesh combination config
            mc = config.mesh_combination
            self.query_one("#mesh-merge-threshold-input", Input).value = str(
                mc.merge_threshold
            )

            self._log("[green]Loaded existing configuration from project[/green]")

        except Exception as e:
            logger.debug(f"Could not load existing config: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "generate-btn":
            self._generate_mesh()
        elif event.button.id == "back-btn":
            self.app.pop_screen()

    def _log(self, message: str) -> None:
        """Add a message to the status log."""
        try:
            status_log = self.query_one("#status-log", RichLog)
            status_log.write(message)
        except Exception:
            # Fallback if RichLog not available yet
            pass

    @work(exclusive=True)
    async def _generate_mesh(self) -> None:
        """Generate mesh from the heightmap."""
        project = self.app.current_project
        if not project:
            self._log("[bold red]ERROR:[/bold red] No current project")
            return

        heightmap_path = project.get_heightmap()
        if not heightmap_path or not heightmap_path.exists():
            self._log(
                "[bold red]ERROR:[/bold red] No heightmap file found. Run Image→Heightmap workflow first."
            )
            return

        # Show loading indicator and disable generate button
        loading = self.query_one("#loading-indicator", LoadingIndicator)
        generate_btn = self.query_one("#generate-btn", Button)
        loading.display = True
        generate_btn.disabled = True
        self.processing = True

        try:
            self._log("[cyan]Building configuration...[/cyan]")
            config = self._build_config()

            self._log(f"[bold]Generating mesh from:[/bold] {heightmap_path.name}")
            self._log("[yellow]This may take several minutes...[/yellow]")

            # Prepare output path
            project.meshes_dir.mkdir(parents=True, exist_ok=True)
            output_path = project.meshes_dir / f"{project.metadata.name}_mesh.stl"

            # Generate mesh
            self._log("[cyan]Processing mesh generation...[/cyan]")
            mesh_data, generator = generate_mesh(
                filepath=heightmap_path,
                config=config,
                save_path=output_path,
            )

            # Update project metadata
            project.set_latest_mesh(output_path)

            # Save config
            project.save_mesh_config(config)

            self._log(
                f"[bold green]SUCCESS![/bold green] Mesh saved: {output_path.name}"
            )
            self._log(
                f"[dim]Vertices: {len(mesh_data.data.vertices)}, Triangles: {len(mesh_data.data.triangles)}[/dim]"
            )
            self._log("[green]Configuration saved to project[/green]")

        except Exception as e:
            self._log(f"[bold red]ERROR:[/bold red] {str(e)}")
            logger.exception("Failed to generate mesh")

        finally:
            # Hide loading indicator and re-enable button
            loading.display = False
            generate_btn.disabled = False
            self.processing = False

    def _build_config(self) -> MeshGenerationConfig:
        """Build MeshGenerationConfig from UI inputs."""

        # Helper to get float value
        def get_float(widget_id: str, default: float) -> float:
            try:
                return float(self.query_one(f"#{widget_id}", Input).value.strip())
            except ValueError:
                self._log(
                    f"[yellow]WARNING:[/yellow] Invalid {widget_id}, using default {default}"
                )
                return default

        # Helper to get int value
        def get_int(widget_id: str, default: int) -> int:
            try:
                return int(self.query_one(f"#{widget_id}", Input).value.strip())
            except ValueError:
                self._log(
                    f"[yellow]WARNING:[/yellow] Invalid {widget_id}, using default {default}"
                )
                return default

        # Build thresholds using linspace
        threshold_start = get_float("threshold-start-input", 0)
        threshold_end = get_float("threshold-end-input", 50)
        threshold_count = get_int("threshold-count-input", 10)
        thresholds = [
            x for x in np.linspace(threshold_start, threshold_end, threshold_count)
        ]

        # Heightmap Processing
        heightmap_processing = HeighmapProcessingConfig(
            exterior_buffer_width=get_int("buffer-width-input", 0),
            exterior_buffer_value=get_float("buffer-value-input", 0.0),
            data_offset=get_float("data-offset-input", 0.0),
            mesh_units=MeshUnits(
                units_x=get_float("units-x-input", 1.0),
                units_y=get_float("units-y-input", 1.0),
                units_z=get_float("units-z-input", 1.0),
            ),
            thresholds=thresholds,
            base_height=get_float("base-height-input", 0.0),
            layer_thickness=get_float("layer-thickness-input", 0.5),
        )

        # Contour Extraction
        contour_extraction = ContourExtractionConfig(
            min_polygon_area=get_float("min-polygon-area-input", 0.01),
            simplify_tolerance=get_float("simplify-tolerance-input", 0.5),
            max_segments=get_int("max-segments-input", 100),
            min_area_fraction=get_float("min-area-fraction-input", 0.01),
        )

        # Triangulation
        triangulation = TriangulationConfig(
            triangulator_add_interior_points=self.query_one(
                "#add-interior-points-checkbox", Checkbox
            ).value,
            triangulator_interior_point_density=get_float(
                "interior-point-density-input", 1.0
            ),
        )

        # Post Processing
        post_processing = PostProcessingConfig(
            apply_post_processing=self.query_one(
                "#apply-post-processing-checkbox", Checkbox
            ).value,
            remove_degenerate_triangles=self.query_one(
                "#remove-degenerate-checkbox", Checkbox
            ).value,
            remove_duplicated_vertices=self.query_one(
                "#remove-dup-vertices-checkbox", Checkbox
            ).value,
            remove_duplicated_triangles=self.query_one(
                "#remove-dup-triangles-checkbox", Checkbox
            ).value,
            remove_unreferenced_vertices=self.query_one(
                "#remove-unref-vertices-checkbox", Checkbox
            ).value,
            merge_close_vertices=self.query_one(
                "#merge-close-vertices-checkbox", Checkbox
            ).value,
            merge_vertices_threshold=get_float("merge-threshold-input", 1e-6),
        )

        # Mesh Combination
        mesh_combination = MeshCombinationConfig(
            merge_threshold=get_float("mesh-merge-threshold-input", 1e-6),
        )

        return MeshGenerationConfig(
            stateless=True,  # Always stateless in TUI
            heightmap_processing=heightmap_processing,
            contour_extraction=contour_extraction,
            triangulation=triangulation,
            post_processing=post_processing,
            mesh_combination=mesh_combination,
        )
