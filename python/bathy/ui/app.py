"""Main application entry point for the Bathymesh TUI.

This module defines the primary BathymeshApp class and handles application-level
concerns like screen navigation and global state.
"""

import logging
from pathlib import Path
from typing import Union

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from bathy.project_manager import Project, ProjectManager
from bathy.ui.screens.main_menu import MainMenuScreen
from bathy.ui.screens.new_project_dialog import NewProjectDialog
from bathy.ui.screens.project_detail import ProjectDetailScreen
from bathy.ui.screens.project_list import ProjectListScreen
from bathy.ui.screens.workflow_image import WorkflowImageScreen
from bathy.ui.screens.workflow_mesh import WorkflowMeshScreen

logger = logging.getLogger(__name__)


class BathymeshApp(App):
    """Bathymesh TUI application for managing mesh generation projects."""

    CSS_PATH = "styles/main.tcss"

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("d", "toggle_dark", "Dark Mode"),
        ("ctrl+c", "quit", "Quit"),
    ]

    SCREENS = {
        "main_menu": MainMenuScreen,
        "project_list": ProjectListScreen,
        "new_project_dialog": NewProjectDialog,
        "project_detail": ProjectDetailScreen,
        "workflow_image": WorkflowImageScreen,
        "workflow_mesh": WorkflowMeshScreen,
    }

    def __init__(self, projects_root: Path, **kwargs):
        """Initialize the Bathymesh TUI application.

        Args:
            projects_root: Root directory containing all projects
            **kwargs: Additional arguments passed to App
        """
        super().__init__(**kwargs)
        self.projects_root = projects_root
        self.project_manager = ProjectManager(projects_root)
        self.current_project: Union[Project, None] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.title = "Bathymesh"
        self.sub_title = "3D Mesh Generation from Heightmaps"

        # Push main menu screen
        self.push_screen("main_menu")

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark


def run_tui(projects_root: Union[str, Path] | None = None) -> None:
    """Run the Bathymesh TUI application.

    Args:
        projects_root: Optional path to projects root directory.
                      Defaults to data/projects relative to repo root.
    """
    if projects_root is None:
        # Find repository root (look for pyproject.toml)
        current = Path.cwd()
        while current != current.parent:
            if (current / "pyproject.toml").exists():
                projects_root = current / "data" / "projects"
                break
            current = current.parent
        else:
            # Fallback to current directory
            projects_root = Path.cwd() / "data" / "projects"
    else:
        projects_root = Path(projects_root)

    projects_root.mkdir(parents=True, exist_ok=True)

    logger.info(f"Starting Bathymesh TUI with projects root: {projects_root}")

    app = BathymeshApp(projects_root)
    app.run()


def main() -> None:
    """Entry point for the 'bathy' command."""
    import sys

    # Configure logging for TUI mode
    # Suppress all library logging to avoid interference with TUI
    log_level = logging.DEBUG if "--debug" in sys.argv else logging.WARNING

    # Configure root logger to suppress most output
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
    )

    # Silence noisy libraries
    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("matplotlib").setLevel(logging.WARNING)
    logging.getLogger("open3d").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    # Only show bathy.ui logs at INFO level in normal mode
    if "--debug" not in sys.argv:
        logging.getLogger("bathy.ui").setLevel(logging.INFO)
        # Suppress workflow logs that would interfere with TUI
        logging.getLogger("bathy.workflows").setLevel(logging.WARNING)
        logging.getLogger("bathy.image_processing").setLevel(logging.WARNING)
        logging.getLogger("bathy.mesh_generator").setLevel(logging.WARNING)

    run_tui()


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    run_tui()
