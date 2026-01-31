"""Main TUI application for bathymesh."""

import logging
from pathlib import Path
from typing import Union

from textual.app import App

from bathy.project_manager import Project, ProjectManager
from bathy.ui.screens import MainMenuScreen

logger = logging.getLogger(__name__)


class BathymeshApp(App):
    """Main TUI application for bathymesh mesh generation.

    Provides a textual user interface for:
    - Managing projects
    - Processing images to heightmaps
    - Generating 3D meshes from heightmaps

    The TUI respects your terminal's color theme by default (ansi_color=True).
    This means colors will match your terminal emulator's theme (e.g., Ghostty,
    iTerm2, Alacritty, etc.). If you prefer Textual's default theme, set
    ansi_color=False when initializing the app.
    """

    # Load multiple CSS files in order
    CSS_PATH = [
        "styles/app.tcss",
        "styles/screens.tcss",
        "styles/widgets.tcss",
        "styles/dialogs.tcss",
    ]
    TITLE = "Bathymesh - 3D Mesh Generator"

    # Application state
    project_manager: ProjectManager
    current_project: Union[Project, None]

    def __init__(self, projects_root: Path, **kwargs) -> None:
        """Initialize BathymeshApp.

        Args:
            projects_root: Root directory for all projects
            **kwargs: Additional arguments for App
        """
        # Use ANSI theme dark mode by default (respects terminal theme)
        if "ansi_color" not in kwargs:
            kwargs["ansi_color"] = True

        super().__init__(**kwargs)
        self.projects_root = projects_root
        self.project_manager = ProjectManager(projects_root)
        self.current_project = None

    def on_mount(self) -> None:
        """Initialize app after mounting."""
        logger.info("Bathymesh TUI started")
        logger.info(f"Projects root: {self.projects_root}")

        # Show main menu
        self.push_screen(MainMenuScreen())

    def action_quit(self) -> None:
        """Exit application."""
        logger.info("Bathymesh TUI exiting")
        self.exit()


def run_tui(projects_root: Union[Path, None] = None, ansi_color: bool = True) -> None:
    """Run the Bathymesh TUI application.

    Args:
        projects_root: Root directory for projects (default: ~/bathymesh_projects)
        ansi_color: Use terminal theme colors (default: True)
    """
    if projects_root is None:
        projects_root = Path(__file__).parent.parent.parent.parent / "data" / "projects"

    # Ensure projects root exists
    projects_root = Path(projects_root)
    projects_root.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=projects_root / "bathymesh_tui.log",
    )

    # Run app with specified color mode
    app = BathymeshApp(projects_root, ansi_color=ansi_color)
    app.run()
