"""Dialog for creating a new project."""

import logging
from typing import Union

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, TextArea

from bathy.project_manager import Project, ProjectError

logger = logging.getLogger(__name__)


class NewProjectDialog(ModalScreen[Union[Project, None]]):
    """Modal dialog for creating a new project.

    Returns a Project instance if created successfully, None if cancelled.
    """

    def compose(self) -> ComposeResult:
        """Compose the dialog UI."""
        with Container():
            yield Label("Create New Project", classes="section-heading", id="title")
            yield Label("Project Name:", id="name-label")
            yield Input(placeholder="my-project", id="name-input")
            yield Label("Description (optional):", id="description-label")
            yield TextArea(id="description-area")
            with Container(id="button-container"):
                yield Button("Create", id="create-button", variant="primary")
                yield Button("Cancel", id="cancel-button")
            yield Label("", id="error-label")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "create-button":
            self._create_project()
        elif event.button.id == "cancel-button":
            self.dismiss(None)

    def _create_project(self) -> None:
        """Create the project and dismiss dialog."""
        name_input = self.query_one("#name-input", Input)
        description_area = self.query_one("#description-area", TextArea)
        error_label = self.query_one("#error-label", Label)

        name = name_input.value.strip()
        description = description_area.text.strip()

        # Validate name
        if not name:
            error_label.update("[bold red]Project name is required[/]")
            return

        # Try to create project
        try:
            # Get project manager from app
            from bathy.ui.app import BathymeshApp

            app = self.app
            if not isinstance(app, BathymeshApp):
                error_label.update("[bold red]Invalid app context[/]")
                return

            project = app.project_manager.create_project(name, description)
            logger.info(f"Created new project: {name}")
            self.dismiss(project)

        except ProjectError as e:
            error_label.update(f"[bold red]{e}[/]")
            logger.error(f"Failed to create project: {e}")
        except Exception as e:
            error_label.update(f"[bold red]Unexpected error: {e}[/]")
            logger.error(f"Unexpected error creating project: {e}", exc_info=True)
