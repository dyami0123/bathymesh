"""New project dialog screen for creating new projects."""

import logging
import re

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.validation import Function, ValidationResult, Validator
from textual.widgets import Button, Input, Label, Static, TextArea

from bathy.project_manager import ProjectError

logger = logging.getLogger(__name__)


class ProjectNameValidator(Validator):
    """Validator for project names."""

    def validate(self, value: str) -> ValidationResult:
        """
        Validate project name.

        Rules:
        - Not empty
        - Only alphanumeric, hyphens, and underscores
        - Not too long (max 50 chars)
        """
        if not value:
            return self.failure("Project name cannot be empty")

        if len(value) > 50:
            return self.failure("Project name must be 50 characters or less")

        # Check for valid characters
        if not re.match(r"^[a-zA-Z0-9_-]+$", value):
            return self.failure(
                "Project name can only contain letters, numbers, hyphens, and underscores"
            )

        return self.success()


class NewProjectDialog(Screen):
    """Dialog screen for creating a new project."""

    CSS = """
    NewProjectDialog {
        align: center middle;
    }
    
    #dialog-container {
        width: 70;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2 4;
    }
    
    #dialog-title {
        width: 100%;
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 2;
    }
    
    .form-field {
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
    
    TextArea {
        width: 100%;
        height: 5;
    }
    
    .error-message {
        width: 100%;
        color: $error;
        text-align: center;
        margin: 1 0;
    }
    
    #button-bar {
        width: 100%;
        height: auto;
        align: center middle;
        margin-top: 2;
    }
    
    #button-bar Button {
        margin: 0 1;
    }
    """

    def __init__(self, **kwargs):
        """Initialize the new project dialog."""
        super().__init__(**kwargs)
        self.error_message = ""

    def compose(self) -> ComposeResult:
        """Create child widgets for the dialog."""
        with Vertical(id="dialog-container"):
            yield Static("➕ New Project", id="dialog-title")

            # Project name field
            with Container(classes="form-field"):
                yield Label("Project Name:", classes="field-label")
                yield Input(
                    placeholder="e.g., hawaii-bathymetry",
                    id="project-name-input",
                    validators=[ProjectNameValidator()],
                )

            # Description field
            with Container(classes="form-field"):
                yield Label("Description (optional):", classes="field-label")
                yield TextArea(id="project-description-input")

            # Error message (hidden by default)
            yield Static("", id="error-msg", classes="error-message")

            # Button bar
            with Horizontal(id="button-bar"):
                yield Button("Create", id="create-btn", variant="success")
                yield Button("Cancel", id="cancel-btn", variant="default")

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Focus the name input
        self.query_one("#project-name-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "create-btn":
            self._create_project()
        elif event.button.id == "cancel-btn":
            self.app.pop_screen()

    def _create_project(self) -> None:
        """Create a new project with the provided information."""
        # Get input values
        name_input = self.query_one("#project-name-input", Input)
        desc_input = self.query_one("#project-description-input", TextArea)
        error_msg = self.query_one("#error-msg", Static)

        name = name_input.value.strip()
        description = desc_input.text.strip()

        # Validate name
        validation = name_input.validate(name)
        if not validation.is_valid:
            # Show error
            error_msg.update(
                validation.failure_descriptions[0]
                if validation.failure_descriptions
                else "Invalid project name"
            )
            return

        try:
            # Create the project
            project = self.app.project_manager.create_project(name, description)

            # Store as current project
            self.app.current_project = project

            logger.info(f"Created new project: {name}")

            # Navigate to project detail screen
            self.app.pop_screen()  # Close dialog
            self.app.push_screen("project_detail")

        except ProjectError as e:
            # Show error
            error_msg.update(str(e))
            logger.error(f"Failed to create project: {e}")
