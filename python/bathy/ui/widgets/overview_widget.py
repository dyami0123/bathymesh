"""Overview widget showing project metadata and file status."""

import logging
from pathlib import Path
from typing import Union

import numpy as np
from PIL import Image
from textual import on, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Button, Label, RichLog, Static, TabbedContent, TabPane
from textual.worker import get_current_worker

from bathy.project_manager import Project
from bathy.ui.widgets.image_preview import InteractiveImagePreview

logger = logging.getLogger(__name__)


class OverviewWidget(Vertical):
    """Project overview tab - displays metadata and file status.

    Shows lightweight project information and provides buttons to load
    detailed file information on demand.
    """

    def __init__(self, project: Project, **kwargs) -> None:
        """Initialize OverviewWidget.

        Args:
            project: Project instance to display
            **kwargs: Additional arguments for Vertical
        """
        super().__init__(**kwargs)
        self._project = project

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        meta = self._project.metadata

        # Project metadata section
        with Container(classes="section"):
            yield Label("Project Information", classes="section-heading")
            yield Static(f"[bold]Name:[/] {meta.name}")
            yield Static(f"[bold]Description:[/] {meta.description or 'None'}")
            yield Static(f"[bold]Status:[/] {meta.status}")
            yield Static(f"[bold]Created:[/] {meta.created[:19]}")
            yield Static(f"[bold]Modified:[/] {meta.modified[:19]}")

        # File status section
        with Container(classes="section"):
            yield Label("File Status", classes="section-heading")

            # Source image
            source_path = self._project.get_source_image()
            if source_path and source_path.exists():
                yield Static(f"[bold]Source Image:[/] {source_path.name}")
                yield Button(
                    "📄 Load Source Info",
                    id="load-source",
                    classes="file-status-button",
                )
            else:
                yield Static("[bold]Source Image:[/] None")

            # Heightmap
            heightmap_path = self._project.get_heightmap()
            if heightmap_path and heightmap_path.exists():
                yield Static(f"[bold]Heightmap:[/] {heightmap_path.name}")
                yield Button(
                    "📊 Load Heightmap Info",
                    id="load-heightmap",
                    classes="file-status-button",
                )
            else:
                yield Static("[bold]Heightmap:[/] None")

            # Mesh
            mesh_path = self._project.get_latest_mesh()
            if mesh_path and mesh_path.exists():
                yield Static(f"[bold]Mesh:[/] {mesh_path.name}")
                yield Button(
                    "🗻 Load Mesh Info", id="load-mesh", classes="file-status-button"
                )
            else:
                yield Static("[bold]Mesh:[/] None")

        # Image preview (if source image exists)
        source_path = self._project.get_source_image()
        if source_path and source_path.exists():
            preview = InteractiveImagePreview(id="image-preview")
            yield preview

        # Info display
        yield RichLog(id="info-log", highlight=True, markup=True)

    def on_mount(self) -> None:
        """Initialize the widget after mounting."""
        # Set image path for preview widget if it exists
        source_path = self._project.get_source_image()
        if source_path and source_path.exists():
            try:
                preview = self.query_one("#image-preview", InteractiveImagePreview)
                preview.set_image_path(source_path)
            except Exception as e:
                logger.warning(f"Could not set image preview path: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press to load file info."""
        if event.button.id == "load-source":
            source_path = self._project.get_source_image()
            if source_path:
                self._load_source_info(source_path)
        elif event.button.id == "load-heightmap":
            heightmap_path = self._project.get_heightmap()
            if heightmap_path:
                self._load_heightmap_info(heightmap_path)
        elif event.button.id == "load-mesh":
            mesh_path = self._project.get_latest_mesh()
            if mesh_path:
                self._load_mesh_info(mesh_path)

    @work(exclusive=True, thread=True)
    def _load_source_info(self, file_path: Path) -> None:
        """Load source image information in worker thread.

        Args:
            file_path: Path to source image
        """
        worker = get_current_worker()
        log = self.query_one("#info-log", RichLog)

        try:
            self.app.call_from_thread(
                log.write, "\n[bold]Loading source image info...[/]"
            )

            # Load image (blocking operation)
            img = Image.open(file_path)
            size_mb = file_path.stat().st_size / (1024 * 1024)

            info = f"""
[bold]Source Image Information:[/]
  Format: {img.format}
  Size: {img.size[0]} x {img.size[1]} pixels
  Mode: {img.mode}
  File Size: {size_mb:.2f} MB
  Path: {file_path}
"""
            if not worker.is_cancelled:
                self.app.call_from_thread(log.write, info)
                logger.info(f"Loaded source image info: {file_path.name}")

        except Exception as e:
            if not worker.is_cancelled:
                error_msg = f"[bold red]Error loading source image:[/] {e}"
                self.app.call_from_thread(log.write, error_msg)
                logger.error(f"Failed to load source info: {e}")

    @work(exclusive=True, thread=True)
    def _load_heightmap_info(self, file_path: Path) -> None:
        """Load heightmap information in worker thread.

        Args:
            file_path: Path to heightmap file
        """
        worker = get_current_worker()
        log = self.query_one("#info-log", RichLog)

        try:
            self.app.call_from_thread(log.write, "\n[bold]Loading heightmap info...[/]")

            # Load heightmap (blocking operation)
            data = np.load(file_path)
            size_mb = file_path.stat().st_size / (1024 * 1024)

            info = f"""
[bold]Heightmap Information:[/]
  Shape: {data.shape}
  Data Type: {data.dtype}
  Min Value: {np.nanmin(data):.3f}
  Max Value: {np.nanmax(data):.3f}
  Mean Value: {np.nanmean(data):.3f}
  NaN Count: {np.count_nonzero(np.isnan(data))}
  File Size: {size_mb:.2f} MB
  Path: {file_path}
"""
            if not worker.is_cancelled:
                self.app.call_from_thread(log.write, info)
                logger.info(f"Loaded heightmap info: {file_path.name}")

        except Exception as e:
            if not worker.is_cancelled:
                error_msg = f"[bold red]Error loading heightmap:[/] {e}"
                self.app.call_from_thread(log.write, error_msg)
                logger.error(f"Failed to load heightmap info: {e}")

    @work(exclusive=True, thread=True)
    def _load_mesh_info(self, file_path: Path) -> None:
        """Load mesh information in worker thread.

        Args:
            file_path: Path to mesh file
        """
        worker = get_current_worker()
        log = self.query_one("#info-log", RichLog)

        try:
            self.app.call_from_thread(log.write, "\n[bold]Loading mesh info...[/]")

            # Just show basic file info for now
            # Full mesh loading would require Open3D which is heavy
            size_mb = file_path.stat().st_size / (1024 * 1024)

            info = f"""
[bold]Mesh Information:[/]
  Format: {file_path.suffix}
  File Size: {size_mb:.2f} MB
  Path: {file_path}
  
  [dim](Full mesh statistics require loading - TBD)[/]
"""
            if not worker.is_cancelled:
                self.app.call_from_thread(log.write, info)
                logger.info(f"Loaded mesh info: {file_path.name}")

        except Exception as e:
            if not worker.is_cancelled:
                error_msg = f"[bold red]Error loading mesh:[/] {e}"
                self.app.call_from_thread(log.write, error_msg)
                logger.error(f"Failed to load mesh info: {e}")
