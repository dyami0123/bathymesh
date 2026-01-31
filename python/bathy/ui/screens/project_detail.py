"""Project detail screen with tabbed workflow interface."""

import logging
from datetime import datetime
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Button, DataTable, Static, TabbedContent, TabPane

logger = logging.getLogger(__name__)


class ProjectDetailScreen(Screen):
    """Screen displaying project details with tabbed workflow interface."""

    CSS = """
    ProjectDetailScreen {
        align: left top;
        padding: 1 2;
    }
    
    #detail-container {
        width: 100%;
        height: 100%;
        background: $surface;
    }
    
    #project-header {
        width: 100%;
        height: auto;
        background: $panel;
        border: solid $accent;
        padding: 1 2;
        margin-bottom: 1;
    }
    
    #project-title {
        width: 100%;
        text-align: left;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #project-description {
        width: 100%;
        text-align: left;
        color: $text-muted;
        margin-bottom: 1;
    }
    
    #project-status {
        width: 100%;
        text-align: left;
        color: $text;
    }
    
    .section-title {
        width: 100%;
        color: $accent;
        text-style: bold;
        margin: 1 0;
    }
    
    .file-info {
        width: 100%;
        color: $text-muted;
        margin: 0 2;
    }
    
    TabbedContent {
        width: 100%;
        height: 1fr;
    }
    
    DataTable {
        height: auto;
        max-height: 10;
        margin: 1 0;
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

    BINDINGS = [
        ("escape", "back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        """Create child widgets for the project detail screen."""
        with Vertical(id="detail-container"):
            # Project header
            with Container(id="project-header"):
                yield Static("", id="project-title")
                yield Static("", id="project-description")
                yield Static("", id="project-status")

            # Tabbed content for workflows and project info
            with TabbedContent():
                # Overview tab
                with TabPane("Overview", id="overview-tab"):
                    with VerticalScroll():
                        yield Static("📁 Project Files", classes="section-title")
                        yield Static("", id="source-image-info", classes="file-info")
                        yield Static("", id="heightmap-info", classes="file-info")
                        yield Static("", id="mesh-info", classes="file-info")

                        yield Static("📜 Workflow History", classes="section-title")
                        table = DataTable(id="history-table")
                        table.cursor_type = "none"
                        yield table

                # Image → Heightmap workflow tab - Import the screen's content
                with TabPane("Image → Heightmap", id="workflow-image-tab"):
                    yield Static("Loading workflow...", id="workflow-image-placeholder")

                # Heightmap → Mesh workflow tab
                with TabPane("Heightmap → Mesh", id="workflow-mesh-tab"):
                    yield Static("Loading workflow...", id="workflow-mesh-placeholder")

            # Button bar
            with Horizontal(id="button-bar"):
                yield Button("Back", id="back-btn", variant="default")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Set up history table
        table = self.query_one("#history-table", DataTable)
        table.add_columns("Time", "Action", "File")

        # Load project data
        self._load_project_data()

        # Mount workflow screens into tabs
        self._mount_workflow_tabs()

    def _mount_workflow_tabs(self) -> None:
        """Mount workflow screen content into the tabs."""
        # Import here to avoid circular imports
        from bathy.ui.screens.workflow_image import WorkflowImageScreen
        from bathy.ui.screens.workflow_mesh import WorkflowMeshScreen

        # Create workflow screen instances
        image_workflow = WorkflowImageScreen()
        mesh_workflow = WorkflowMeshScreen()

        # Mount their content into our tabs
        # Note: This is a simplified approach - we'll just show placeholders
        # and handle tab switching to push the actual screens
        pass

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """Handle tab activation."""
        if event.pane.id == "workflow-image-tab":
            # Push the actual workflow screen
            self.app.push_screen("workflow_image")
        elif event.pane.id == "workflow-mesh-tab":
            self.app.push_screen("workflow_mesh")

    def _load_project_data(self) -> None:
        """Load and display project data."""
        project = self.app.current_project

        if project is None:
            logger.error("No current project set")
            self.app.pop_screen()
            return

        # Update header
        title = self.query_one("#project-title", Static)
        title.update(f"📂 {project.metadata.name}")

        desc = self.query_one("#project-description", Static)
        desc.update(project.metadata.description or "No description")

        # Status with emoji
        status_map = {
            "none": "🆕 New",
            "image_loaded": "🖼️  Image Loaded",
            "heightmap_generated": "🗺️  Heightmap Generated",
            "mesh_generated": "✅ Mesh Generated",
        }
        status = self.query_one("#project-status", Static)
        status_str = status_map.get(project.metadata.status, project.metadata.status)

        # Add modified time
        try:
            dt = datetime.fromisoformat(project.metadata.modified)
            modified_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            modified_str = project.metadata.modified[:16]

        status.update(f"Status: {status_str} | Modified: {modified_str}")

        # Update file info
        source_info = self.query_one("#source-image-info", Static)
        if project.metadata.source_image:
            source_path = project.project_dir / project.metadata.source_image
            if source_path.exists():
                size_mb = source_path.stat().st_size / (1024 * 1024)
                source_info.update(
                    f"  Source Image: {source_path.name} ({size_mb:.2f} MB)"
                )
            else:
                source_info.update(
                    f"  Source Image: {project.metadata.source_image} (not found)"
                )
        else:
            source_info.update("  Source Image: None")

        heightmap_info = self.query_one("#heightmap-info", Static)
        if project.metadata.heightmap_file:
            heightmap_path = project.project_dir / project.metadata.heightmap_file
            if heightmap_path.exists():
                size_mb = heightmap_path.stat().st_size / (1024 * 1024)
                heightmap_info.update(
                    f"  Heightmap: {heightmap_path.name} ({size_mb:.2f} MB)"
                )
            else:
                heightmap_info.update(
                    f"  Heightmap: {project.metadata.heightmap_file} (not found)"
                )
        else:
            heightmap_info.update("  Heightmap: None")

        mesh_info = self.query_one("#mesh-info", Static)
        if project.metadata.latest_mesh:
            mesh_path = project.project_dir / project.metadata.latest_mesh
            if mesh_path.exists():
                size_mb = mesh_path.stat().st_size / (1024 * 1024)
                mesh_info.update(f"  Latest Mesh: {mesh_path.name} ({size_mb:.2f} MB)")
            else:
                mesh_info.update(
                    f"  Latest Mesh: {project.metadata.latest_mesh} (not found)"
                )
        else:
            mesh_info.update("  Latest Mesh: None")

        # Load workflow history
        table = self.query_one("#history-table", DataTable)
        table.clear()

        for entry in reversed(
            project.metadata.workflow_history[-10:]
        ):  # Last 10 entries
            try:
                dt = datetime.fromisoformat(entry["timestamp"])
                time_str = dt.strftime("%H:%M:%S")
            except Exception:
                time_str = entry["timestamp"][:8]

            action = entry.get("action", "unknown")
            file_path = entry.get("file", "")

            # Shorten file path
            if len(file_path) > 30:
                file_path = "..." + file_path[-27:]

            table.add_row(time_str, action, file_path)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "back-btn":
            self.app.pop_screen()

    def action_back(self) -> None:
        """Handle back action."""
        self.app.pop_screen()
