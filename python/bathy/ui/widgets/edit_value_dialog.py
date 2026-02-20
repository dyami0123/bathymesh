"""Dialog for editing a single configuration value."""

from typing import Union

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label


class EditValueDialog(ModalScreen[Union[str, None]]):
    """Modal dialog for editing a configuration value.

    Returns the new value as string, or None if cancelled.
    """

    def __init__(
        self,
        param_name: str,
        current_value: str,
        description: Union[str, None] = None,
        **kwargs,
    ) -> None:
        """Initialize EditValueDialog.

        Args:
            param_name: Name of parameter being edited
            current_value: Current value as string
            description: Optional description from config metadata
            **kwargs: Additional arguments for ModalScreen
        """
        super().__init__(**kwargs)
        self._param_name = param_name
        self._current_value = current_value
        self._description = description

    def compose(self) -> ComposeResult:
        """Compose the dialog UI."""
        with Container():
            yield Label(
                f"Edit: {self._param_name}", classes="section-heading", id="title"
            )

            # Show description if available
            if self._description:
                yield Label(
                    f"[dim]{self._description}[/]",
                    id="description",
                )

            yield Label(
                "[dim]Type: bool (True/False), number (123, 1.5), text, or None[/]",
                id="help-text",
            )
            yield Label(
                "[dim]Press Enter to save, Esc to cancel[/]",
                id="shortcuts-text",
            )
            yield Input(value=self._current_value, id="value-input")
            with Container(id="button-container"):
                yield Button("Save", id="save-button", variant="primary")
                yield Button("Cancel", id="cancel-button")

    def on_mount(self) -> None:
        """Focus input on mount."""
        self.query_one("#value-input", Input).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "save-button":
            value_input = self.query_one("#value-input", Input)
            self.dismiss(value_input.value)
        elif event.button.id == "cancel-button":
            self.dismiss(None)

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "escape":
            self.dismiss(None)
            event.prevent_default()
        if event.key == "enter":
            value_input = self.query_one("#value-input", Input)
            self.dismiss(value_input.value)
            event.prevent_default()
