"""Modal screen for displaying long-running processing operations with streaming logs."""

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Label, LoadingIndicator, RichLog


class ProcessingModal(ModalScreen[bool]):
    """Modal screen with streaming logs for long-running operations.

    Shows a loading indicator and streams log messages in real-time.
    Returns True on success, False on failure/cancel.
    """

    def __init__(self, title: str, **kwargs) -> None:
        """Initialize ProcessingModal.

        Args:
            title: Title to display in the modal
            **kwargs: Additional arguments for ModalScreen
        """
        super().__init__(**kwargs)
        self._title = title
        self._is_complete = False

    def compose(self) -> ComposeResult:
        """Compose the modal UI."""
        with Container():
            yield Label(self._title, id="title-label")
            yield LoadingIndicator(id="loading-indicator")
            yield RichLog(id="log-viewer", highlight=True, markup=True)
            yield Label("Processing...", id="status-label")
            yield Button("Close", id="close-button", variant="primary", disabled=True)

    def append_log(self, message: str) -> None:
        """Append a log message to the viewer.

        This method is thread-safe and should be called via call_from_thread.

        Args:
            message: Log message to append
        """
        log_viewer = self.query_one("#log-viewer", RichLog)
        log_viewer.write(message)

    def mark_complete(self, success: bool, message: str) -> None:
        """Mark the operation as complete.

        This method is thread-safe and should be called via call_from_thread.

        Args:
            success: True if operation succeeded, False otherwise
            message: Final status message
        """
        self._is_complete = True

        # Hide loading indicator
        loading = self.query_one("#loading-indicator", LoadingIndicator)
        loading.display = False

        # Update status
        status_label = self.query_one("#status-label", Label)
        status_label.update(message)

        # Enable close button
        close_button = self.query_one("#close-button", Button)
        close_button.disabled = False

        # Add final log message
        if success:
            self.append_log(f"\n[bold green]{message}[/]")
        else:
            self.append_log(f"\n[bold red]{message}[/]")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "close-button" and self._is_complete:
            self.dismiss(True)
