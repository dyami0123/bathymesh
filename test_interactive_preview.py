#!/usr/bin/env python3
"""Test script for InteractiveImagePreview widget."""

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical

from bathy.ui.widgets.image_preview import InteractiveImagePreview


class TestPreviewApp(App):
    """Test application for InteractiveImagePreview."""

    CSS_PATH = "python/bathy/ui/styles/widgets.tcss"

    CSS = """
    Screen {
        background: $surface;
        align: center middle;
    }
    
    Vertical {
        width: 90%;
        height: auto;
    }
    """

    def __init__(self, image_path: Path):
        super().__init__()
        self.image_path = image_path

    def compose(self) -> ComposeResult:
        """Compose the test UI."""
        with Vertical():
            preview = InteractiveImagePreview(id="test-preview")
            yield preview

    def on_mount(self) -> None:
        """Set image path after mounting."""
        preview = self.query_one("#test-preview", InteractiveImagePreview)
        preview.set_image_path(self.image_path)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_interactive_preview.py <image_path>")
        print("Example: python test_interactive_preview.py data/processed/hawaii.png")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)

    app = TestPreviewApp(image_path)
    app.run()
