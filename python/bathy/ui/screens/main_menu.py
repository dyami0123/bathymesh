"""Main menu screen for the Bathymesh TUI."""

from textual.app import ComposeResult
from textual.containers import Center, Middle, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


class MainMenuScreen(Screen):
    """Main menu screen - entry point for the application."""

    CSS = """
    MainMenuScreen {
        align: center middle;
    }
    
    #menu-container {
        width: 60;
        height: auto;
        border: thick $primary;
        background: $surface;
        padding: 2 4;
    }
    
    #title {
        width: 100%;
        text-align: center;
        color: $accent;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #subtitle {
        width: 100%;
        text-align: center;
        color: $text-muted;
        margin-bottom: 2;
    }
    
    Button {
        width: 100%;
        margin: 1 0;
    }
    """

    def compose(self) -> ComposeResult:
        """Create child widgets for the main menu."""
        with Center():
            with Middle():
                with Vertical(id="menu-container"):
                    yield Static("🌊 BATHYMESH", id="title")
                    yield Static("3D Mesh Generation from Heightmaps", id="subtitle")
                    yield Button(
                        "📂 Open Project", id="open-project", variant="primary"
                    )
                    yield Button("➕ New Project", id="new-project", variant="success")
                    yield Button("❌ Exit", id="exit", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        if event.button.id == "open-project":
            self.app.push_screen("project_list")
        elif event.button.id == "new-project":
            self.app.push_screen("new_project_dialog")
        elif event.button.id == "exit":
            self.app.exit()
