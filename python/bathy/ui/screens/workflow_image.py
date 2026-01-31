"""Image to Heightmap workflow screen."""

import logging
from pathlib import Path
from typing import Optional

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import (
    Button,
    Checkbox,
    DirectoryTree,
    Input,
    Label,
    LoadingIndicator,
    RichLog,
    Static,
    TextArea,
)

from bathy.config import ImageProcessingConfig
from bathy.project_manager import ProjectError
from bathy.workflows.process_image import process_image

logger = logging.getLogger(__name__)


class WorkflowImageScreen(Screen):
    """Screen for Image → Heightmap workflow."""

    CSS = """
    WorkflowImageScreen {
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
        layout: horizontal;
    }
    
    #left-panel {
        width: 50%;
        height: 100%;
        padding: 0 1 0 0;
    }
    
    #right-panel {
        width: 50%;
        height: 100%;
        padding: 0 0 0 1;
    }
    
    .section {
        width: 100%;
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-bottom: 1;
    }
    
    .section-title {
        width: 100%;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    DirectoryTree {
        height: 20;
        border: solid $primary;
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
    }
    
    #color-map-input {
        width: 100%;
        height: 8;
        border: solid $primary;
    }
    
    #status-area {
        width: 100%;
        height: 12;
        border: solid $primary;
        padding: 0;
        background: $panel;
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

    def __init__(self, **kwargs):
        """Initialize the workflow screen."""
        super().__init__(**kwargs)
        self.selected_file: Optional[Path] = None
        self.processing = False

    def compose(self) -> ComposeResult:
        """Create child widgets for the workflow screen."""
        with Vertical(id="workflow-container"):
            # Header
            with Container(id="workflow-header"):
                yield Static("🖼️  Image → Heightmap Workflow", id="workflow-title")

            # Content area with two panels
            with Horizontal(id="content-area"):
                # Left panel - File selection
                with Vertical(id="left-panel"):
                    with Container(classes="section"):
                        yield Static("1. Select Source Image", classes="section-title")
                        yield DirectoryTree(
                            str(Path.home()),
                            id="file-tree",
                        )
                        yield Static("No file selected", id="selected-file-display")

                    # Or use current source if available
                    with Container(classes="section"):
                        yield Static(
                            "Or use current project source:", classes="field-label"
                        )
                        yield Button(
                            "Use Project Source Image",
                            id="use-current-btn",
                            variant="default",
                        )

                # Right panel - Configuration
                with Vertical(id="right-panel"):
                    with Container(classes="section"):
                        yield Static("2. Configuration", classes="section-title")

                        # Basic settings
                        with Container(classes="field"):
                            yield Label(
                                "Max Dimension (optional):", classes="field-label"
                            )
                            yield Input(
                                placeholder="e.g., 2048 (leave empty for full resolution)",
                                id="max-dimension-input",
                            )

                        with Container(classes="field"):
                            yield Checkbox(
                                "Fill NaN values", id="fill-nan-checkbox", value=True
                            )

                        with Container(classes="field"):
                            yield Label("Fill Max Iterations:", classes="field-label")
                            yield Input(value="100", id="fill-iterations-input")

                        with Container(classes="field"):
                            yield Label(
                                "Color Map (Python dict format):", classes="field-label"
                            )
                            yield TextArea(
                                id="color-map-input",
                                text='{\n  "#0000FF": {"value": -10.0, "fuzziness": 5.0},\n  "#00FFFF": {"value": -5.0, "fuzziness": 5.0},\n  "#00FF00": {"value": 0.0, "fuzziness": 5.0},\n  "#FFFF00": {"value": 5.0, "fuzziness": 5.0},\n  "#FF0000": {"value": 10.0, "fuzziness": 5.0}\n}',
                            )

            # Status area with loading indicator and log
            with Container(id="status-area"):
                yield LoadingIndicator(id="loading-indicator")
                yield RichLog(id="status-log", highlight=True, markup=True)

            # Button bar
            with Horizontal(id="button-bar"):
                yield Button("Process", id="process-btn", variant="success")
                yield Button("Back", id="back-btn", variant="default")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Hide loading indicator initially
        self.query_one("#loading-indicator", LoadingIndicator).display = False

        # Log initial message
        self._log("[bold green]Ready to process image[/bold green]")

        # Check if project has existing source image
        project = self.app.current_project
        if project and project.metadata.source_image:
            source_path = project.get_source_image()
            if source_path and source_path.exists():
                self.selected_file = source_path
                display = self.query_one("#selected-file-display", Static)
                display.update(f"Selected: {source_path.name}")

    def on_directory_tree_file_selected(
        self, event: DirectoryTree.FileSelected
    ) -> None:
        """Handle file selection from directory tree."""
        self.selected_file = event.path
        display = self.query_one("#selected-file-display", Static)
        display.update(f"Selected: {event.path.name}")
        logger.debug(f"Selected file: {event.path}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "use-current-btn":
            self._use_current_source()
        elif event.button.id == "process-btn":
            self._process_image()
        elif event.button.id == "back-btn":
            self.app.pop_screen()

    def _use_current_source(self) -> None:
        """Use the project's current source image."""
        project = self.app.current_project
        if project and project.metadata.source_image:
            source_path = project.get_source_image()
            if source_path and source_path.exists():
                self.selected_file = source_path
                display = self.query_one("#selected-file-display", Static)
                display.update(f"Selected: {source_path.name}")
                self._log("Using current project source image")
            else:
                self._log("ERROR: Project source image not found")
        else:
            self._log("ERROR: No source image in project")

    def _log(self, message: str) -> None:
        """Add a message to the status log."""
        try:
            status_log = self.query_one("#status-log", RichLog)
            status_log.write(message)
        except Exception:
            # Fallback if RichLog not available yet
            pass

    @work(exclusive=True)
    async def _process_image(self) -> None:
        """Process the selected image to generate a heightmap."""
        if self.selected_file is None:
            self._log("[bold red]ERROR:[/bold red] No image file selected")
            return

        project = self.app.current_project
        if project is None:
            self._log("[bold red]ERROR:[/bold red] No current project")
            return

        # Show loading indicator and disable process button
        loading = self.query_one("#loading-indicator", LoadingIndicator)
        process_btn = self.query_one("#process-btn", Button)
        loading.display = True
        process_btn.disabled = True
        self.processing = True

        try:
            self._log("[cyan]Building configuration...[/cyan]")

            # Get configuration from inputs
            config = self._build_config()

            self._log(f"[bold]Processing image:[/bold] {self.selected_file.name}")
            self._log("[yellow]This may take a while...[/yellow]")

            # Set source image in project if it's not already set
            if (
                not project.metadata.source_image
                or project.get_source_image() != self.selected_file
            ):
                project.set_source_image(self.selected_file)
                self._log("[green]Source image added to project[/green]")

            # Prepare output path
            project.heightmap_dir.mkdir(parents=True, exist_ok=True)
            output_path = (
                project.heightmap_dir / f"{project.metadata.name}_heightmap.npy"
            )

            # Process the image
            self._log("[cyan]Processing... (loading image)[/cyan]")
            result = process_image(
                image_path=self.selected_file,
                config=config,
                save_path=output_path,
            )

            # Update project metadata
            project.set_heightmap(output_path)

            # Save config
            project.save_image_config(config)

            self._log(
                f"[bold green]SUCCESS![/bold green] Heightmap saved: {output_path.name}"
            )
            self._log(
                f"[dim]Shape: {result.shape}, Min: {result.min():.2f}, Max: {result.max():.2f}[/dim]"
            )
            self._log("[green]Configuration saved to project[/green]")

        except Exception as e:
            self._log(f"[bold red]ERROR:[/bold red] {str(e)}")
            logger.exception("Failed to process image")

        finally:
            # Hide loading indicator and re-enable button
            loading.display = False
            process_btn.disabled = False
            self.processing = False

    def _build_config(self) -> ImageProcessingConfig:
        """Build ImageProcessingConfig from UI inputs."""
        from collections import OrderedDict

        # Get max dimension
        max_dim_input = self.query_one("#max-dimension-input", Input)
        max_dimension = None
        if max_dim_input.value.strip():
            try:
                max_dimension = int(max_dim_input.value.strip())
            except ValueError:
                self._log("WARNING: Invalid max dimension, using full resolution")

        # Get fill NaN setting
        fill_nan = self.query_one("#fill-nan-checkbox", Checkbox).value

        # Get fill iterations
        fill_iterations_input = self.query_one("#fill-iterations-input", Input)
        try:
            fill_iterations = int(fill_iterations_input.value.strip())
        except ValueError:
            fill_iterations = 100
            self._log("WARNING: Invalid fill iterations, using 100")

        # Parse color map
        color_map_input = self.query_one("#color-map-input", TextArea)
        color_map_text = color_map_input.text.strip()

        try:
            # Evaluate the Python dict literal
            color_map_dict = eval(color_map_text)
            color_map = OrderedDict(color_map_dict)
        except Exception as e:
            self._log(f"WARNING: Invalid color map format, using default. Error: {e}")
            color_map = OrderedDict(
                {
                    "#0000FF": {"value": -10.0, "fuzziness": 5.0},
                    "#00FFFF": {"value": -5.0, "fuzziness": 5.0},
                    "#00FF00": {"value": 0.0, "fuzziness": 5.0},
                    "#FFFF00": {"value": 5.0, "fuzziness": 5.0},
                    "#FF0000": {"value": 10.0, "fuzziness": 5.0},
                }
            )

        return ImageProcessingConfig(
            preserve_full_resolution=(max_dimension is None),
            max_dimension=max_dimension,
            fill_nan_values=fill_nan,
            fill_max_iterations=fill_iterations,
            color_map=color_map,
        )
