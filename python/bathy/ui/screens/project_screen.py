"""Project screen with tabbed interface for workflows."""

import logging

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, TabbedContent, TabPane

from bathy.project_manager import Project
from bathy.ui.widgets import ImageWorkflowWidget, MeshWorkflowWidget, OverviewWidget

logger = logging.getLogger(__name__)


class ProjectScreen(Screen):
    """Main project screen with tabs for different workflows.

    Displays project metadata and provides tabs for:
    - Overview: Project information and file status
    - Image → Heightmap: Image processing workflow
    - Heightmap → Mesh: Mesh generation workflow
    """

    BINDINGS = [
        ("escape", "back", "Back to Projects"),
    ]

    def __init__(self, project: Project, **kwargs) -> None:
        """Initialize ProjectScreen.

        Args:
            project: Project instance to display
            **kwargs: Additional arguments for Screen
        """
        super().__init__(**kwargs)
        self._project = project

    def compose(self) -> ComposeResult:
        """Compose the screen UI."""
        yield Header()

        # Project header
        with Container(id="project-header"):
            meta = self._project.metadata
            yield Label(
                f"Project: {meta.name}", classes="section-heading", id="project-title"
            )
            if meta.description:
                yield Label(f"[dim]{meta.description}[/]", id="project-description")

        # Tabbed content
        with TabbedContent(initial="tab-overview"):
            with TabPane("Overview", id="tab-overview"):
                yield OverviewWidget(project=self._project)

            with TabPane("Image → Heightmap", id="tab-image"):
                yield ImageWorkflowWidget(project=self._project)

            with TabPane("Heightmap → Mesh", id="tab-mesh"):
                yield MeshWorkflowWidget(project=self._project)

        # Back button
        yield Button("← Back to Projects", id="back-button")

        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "back-button":
            self.action_back()

    def action_back(self) -> None:
        """Return to main menu."""
        self.app.pop_screen()
        logger.debug("Returned to main menu from project screen")
