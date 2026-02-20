"""Image workflow widget for processing images into heightmaps."""

import logging
from pathlib import Path
from typing import Union

from PIL import Image
from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, Label, RichLog, Static
from textual.worker import get_current_worker

from bathy.config import ImageProcessingConfig
from bathy.project_manager import Project
from bathy.ui.widgets.color_map_widget import ColorMapWidget
from bathy.ui.widgets.config_table import ConfigTable
from bathy.ui.widgets.processing_modal import ProcessingModal
from bathy.workflows.process_image import process_image

logger = logging.getLogger(__name__)


class ImageWorkflowWidget(Vertical):
    """Image → Heightmap workflow tab.

    Allows user to select an image, configure processing parameters,
    preview file info, and process the image to generate a heightmap.
    """

    def __init__(self, project: Project, **kwargs) -> None:
        """Initialize ImageWorkflowWidget.

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
            yield Label("Source Image Selection", classes="section-heading")
            yield Input(placeholder="/path/to/image.png", id="file-input")
            yield Button("📂 Use Project Source", id="use-source-button")

        # File info section (initially empty)
        with Container(id="file-info-container") as info_container:
            info_container.display = False
            yield Label(
                "File Information", classes="section-heading", id="file-info-label"
            )
            yield Static("", id="file-info-text")

        # Configuration section
        with Container(classes="section"):
            yield Label("Processing Configuration", classes="section-heading")
            config_table = ConfigTable(id="config-table")
            yield config_table

        # Color Map section (will be populated on mount)
        with Container(classes="section", id="color-map-section"):
            pass

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
            config = self._project.load_image_config()
            logger.debug("Loaded existing image config")
        except Exception as e:
            logger.warning(f"Could not load config, using defaults: {e}")
            config = ImageProcessingConfig()

        # Populate config table
        config_table = self.query_one("#config-table", ConfigTable)
        config_table.load_config(config)

        # Add ColorMapWidget to color map section
        color_map_section = self.query_one("#color-map-section", Container)
        color_map_widget = ColorMapWidget(config.color_map, id="color-map-widget")
        color_map_section.mount(color_map_widget)

        # Pre-fill source if available
        source_path = self._project.get_source_image()
        if source_path:
            file_input = self.query_one("#file-input", Input)
            file_input.value = str(source_path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "use-source-button":
            self._use_project_source()
        elif event.button.id == "preview-button":
            self._preview_file()
        elif event.button.id == "process-button":
            self._start_processing()

    def _use_project_source(self) -> None:
        """Fill input with project source image path."""
        source_path = self._project.get_source_image()
        if source_path:
            file_input = self.query_one("#file-input", Input)
            file_input.value = str(source_path)

            status_log = self.query_one("#status-log", RichLog)
            status_log.write(f"[green]Set path to project source: {source_path}[/]")
        else:
            status_log = self.query_one("#status-log", RichLog)
            status_log.write("[yellow]No source image set in project[/]")

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
        """Load file information in worker thread.

        Args:
            file_path: Path to image file
        """
        worker = get_current_worker()
        status_log = self.query_one("#status-log", RichLog)

        try:
            self.app.call_from_thread(status_log.write, "Loading file info...")

            # Load image (blocking operation)
            img = Image.open(file_path)
            size_mb = file_path.stat().st_size / (1024 * 1024)

            info_text = f"""Format: {img.format}
Size: {img.size[0]} x {img.size[1]} pixels
Mode: {img.mode}
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

        # Build config from table and ColorMapWidget
        config_table = self.query_one("#config-table", ConfigTable)
        config_dict = config_table.get_config_dict()

        color_map_widget = self.query_one("#color-map-widget", ColorMapWidget)
        color_map = color_map_widget.get_color_map()

        # Reconstruct ImageProcessingConfig with edited values
        config = ImageProcessingConfig(
            preserve_full_resolution=config_dict.get("preserve_full_resolution", True),
            max_dimension=config_dict.get("max_dimension"),
            region=self._parse_region(config_dict.get("region")),
            fill_nan_values=config_dict.get("fill_nan_values", True),
            fill_max_iterations=config_dict.get("fill_max_iterations", 100),
            fill_neighborhood=config_dict.get("fill_neighborhood", 1),
            color_map=color_map,
            default_fuzziness=config_dict.get("default_fuzziness", 10.0),
        )

        # Save config to project
        try:
            self._project.save_image_config(config)
            logger.debug("Saved image config to project")
        except Exception as e:
            logger.warning(f"Could not save config: {e}")

        # Show processing modal
        modal = ProcessingModal(title="Processing Image → Heightmap")
        self.app.push_screen(modal)

        # Start processing in worker
        self._run_processing(file_path, config, modal)

    def _parse_region(
        self, region_value: Union[str, tuple, None]
    ) -> Union[tuple[int, int, int, int], None]:
        """Parse region from string or return as-is.

        Args:
            region_value: Region value from config table (string, tuple, or None)

        Returns:
            Tuple of (left, upper, right, lower) or None
        """
        if region_value is None:
            return None

        if isinstance(region_value, tuple):
            return region_value

        # Parse from string format: "(left, upper, right, lower)"
        if isinstance(region_value, str):
            try:
                # Remove parentheses and split
                region_str = region_value.strip("() ")
                if not region_str:
                    return None
                parts = [int(x.strip()) for x in region_str.split(",")]
                if len(parts) == 4:
                    return tuple(parts)  # type: ignore
            except (ValueError, AttributeError):
                logger.warning(f"Could not parse region value: {region_value}")
                return None

        return None

    @work(exclusive=True, thread=True)
    def _run_processing(
        self, file_path: Path, config: ImageProcessingConfig, modal: ProcessingModal
    ) -> None:
        """Run image processing workflow in worker thread.

        Args:
            file_path: Path to source image
            config: Processing configuration
            modal: Modal to update with progress
        """
        worker = get_current_worker()

        try:
            # Log start
            self.app.call_from_thread(modal.append_log, "Starting image processing...")
            self.app.call_from_thread(modal.append_log, f"Source: {file_path}")
            self.app.call_from_thread(modal.append_log, "")

            if worker.is_cancelled:
                return

            # Determine output path
            heightmap_dir = self._project.heightmap_dir
            heightmap_dir.mkdir(exist_ok=True)
            output_path = heightmap_dir / f"{file_path.stem}_heightmap.npy"

            self.app.call_from_thread(modal.append_log, f"Output: {output_path}")
            self.app.call_from_thread(modal.append_log, "")

            if worker.is_cancelled:
                return

            # Run workflow (blocking operation)
            self.app.call_from_thread(modal.append_log, "Loading image...")
            result = process_image(file_path, config, save_path=output_path)

            if worker.is_cancelled:
                return

            self.app.call_from_thread(
                modal.append_log, f"Generated heightmap shape: {result.shape}"
            )
            self.app.call_from_thread(modal.append_log, f"Saved to: {output_path}")

            # Update project metadata
            self._project.set_heightmap(output_path)

            self.app.call_from_thread(modal.append_log, "")
            self.app.call_from_thread(
                modal.mark_complete, True, "✓ Image processing complete!"
            )

            # Update status log
            status_log = self.query_one("#status-log", RichLog)
            self.app.call_from_thread(
                status_log.write,
                f"[bold green]✓ Successfully generated heightmap: {output_path.name}[/]",
            )

            logger.info(f"Image processing complete: {output_path}")

        except Exception as e:
            if not worker.is_cancelled:
                error_msg = f"✗ Processing failed: {e}"
                self.app.call_from_thread(modal.mark_complete, False, error_msg)

                status_log = self.query_one("#status-log", RichLog)
                self.app.call_from_thread(status_log.write, f"[bold red]{error_msg}[/]")

                logger.error(f"Image processing failed: {e}", exc_info=True)
