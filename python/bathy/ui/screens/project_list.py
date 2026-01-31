"""Project list screen for browsing and selecting projects."""

import logging
from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Static

from bathy.project_manager import ProjectError, ProjectInfo

logger = logging.getLogger(__name__)


class ProjectListScreen(Screen):
    """Screen for listing and selecting projects."""

    CSS = """
    ProjectListScreen {
        align: center top;
        padding: 2 4;
    }
    
    #project-list-container {
        width: 100%;
        height: 100%;
        border: thick $primary;
        background: $surface;
        padding: 2;
    }
    
    #header {
        width: 100%;
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #info-text {
        width: 100%;
        text-align: center;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    DataTable {
        height: 1fr;
        margin: 1 0;
    }
    
    #button-bar {
        width: 100%;
        height: auto;
        align: center middle;
    }
    
    #button-bar Button {
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs):
        """Initialize the project list screen."""
        super().__init__(**kwargs)
        self.selected_project: Optional[ProjectInfo] = None

    def compose(self) -> ComposeResult:
        """Create child widgets for the project list."""
        with Vertical(id="project-list-container"):
            yield Static("📂 Projects", id="header")
            yield Static("Select a project to open", id="info-text")

            # DataTable to display projects
            table = DataTable(id="project-table")
            table.cursor_type = "row"
            yield table

            # Button bar
            with Horizontal(id="button-bar"):
                yield Button("Open", id="open-btn", variant="primary")
                yield Button("Delete", id="delete-btn", variant="error")
                yield Button("Back", id="back-btn", variant="default")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        table = self.query_one(DataTable)

        # Set up columns
        table.add_columns("Name", "Description", "Status", "Modified")

        # Load projects from project manager
        self._refresh_project_list()

    def _refresh_project_list(self) -> None:
        """Refresh the project list from the project manager."""
        table = self.query_one(DataTable)
        table.clear()

        try:
            projects = self.app.project_manager.list_projects()

            if not projects:
                # Update info text to show no projects
                info_text = self.query_one("#info-text", Static)
                info_text.update(
                    "No projects found. Create a new project to get started."
                )
            else:
                # Add rows for each project
                for project in projects:
                    # Format modified time nicely
                    try:
                        from datetime import datetime

                        dt = datetime.fromisoformat(project.modified)
                        modified_str = dt.strftime("%Y-%m-%d %H:%M")
                    except Exception:
                        modified_str = project.modified[:16]  # Fallback

                    # Truncate description if too long
                    desc = (
                        project.description[:40] + "..."
                        if len(project.description) > 40
                        else project.description
                    )

                    # Status formatting
                    status_map = {
                        "none": "New",
                        "image_loaded": "Image Loaded",
                        "heightmap_generated": "Heightmap Ready",
                        "mesh_generated": "Mesh Generated",
                    }
                    status = status_map.get(project.status, project.status)

                    table.add_row(
                        project.name,
                        desc,
                        status,
                        modified_str,
                        key=project.name,
                    )

            logger.info(f"Loaded {len(projects)} projects")

        except Exception as e:
            logger.error(f"Failed to load projects: {e}")
            info_text = self.query_one("#info-text", Static)
            info_text.update(f"Error loading projects: {e}")

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        """Handle row selection in the data table."""
        table = self.query_one(DataTable)
        row_key = event.row_key

        # Find the project by name (row key is project name)
        projects = self.app.project_manager.list_projects()
        for project in projects:
            if project.name == row_key:
                self.selected_project = project
                logger.debug(f"Selected project: {project.name}")
                break

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        """Handle row highlight (cursor move) in the data table."""
        if event.row_key is None:
            return

        # Update selected project when cursor moves
        projects = self.app.project_manager.list_projects()
        for project in projects:
            if project.name == event.row_key:
                self.selected_project = project
                logger.debug(f"Highlighted project: {project.name}")
                break

    def on_key(self, event) -> None:
        """Handle key press events."""
        if event.key == "enter" and self.selected_project:
            self._open_selected_project()
            event.prevent_default()
            event.stop()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "open-btn":
            self._open_selected_project()
        elif event.button.id == "delete-btn":
            self._delete_selected_project()
        elif event.button.id == "back-btn":
            self.app.pop_screen()

    def _open_selected_project(self) -> None:
        """Open the selected project."""
        if self.selected_project is None:
            # Show notification if available
            logger.warning("No project selected")
            return

        try:
            # Load the project
            project = self.app.project_manager.load_project(self.selected_project.name)

            # Store current project in app state
            self.app.current_project = project

            # Navigate to project detail screen
            self.app.push_screen("project_detail")

            logger.info(f"Opened project: {project.metadata.name}")

        except ProjectError as e:
            logger.error(f"Failed to open project: {e}")

    def _delete_selected_project(self) -> None:
        """Delete the selected project after confirmation."""
        if self.selected_project is None:
            logger.warning("No project selected")
            return

        # TODO: Add confirmation dialog
        # For now, just log that we would delete
        logger.warning(f"Delete requested for project: {self.selected_project.name}")
        logger.warning(
            "Delete functionality requires confirmation dialog - not implemented yet"
        )
