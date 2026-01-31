"""Test script to verify image click handling and pixel color picking."""

from pathlib import Path
from PIL import Image as PILImage
from textual import events
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Label, Static
from textual_image.widget import Image


class ImageClickTestApp(App):
    """Test app for image click handling."""

    CSS = """
    Screen {
        align: center middle;
    }
    
    Vertical {
        width: auto;
        height: auto;
        border: solid $accent;
        padding: 1;
    }
    
    #test-image {
        border: solid $primary;
        margin: 1;
    }
    
    #info {
        text-align: center;
        margin: 1;
        background: $boost;
        padding: 1;
        border: solid $panel;
    }
    """

    def __init__(self, image_path: Path):
        super().__init__()
        self.image_path = image_path
        self.pil_image = None

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        with Vertical():
            yield Label("Image Click Test", classes="section-heading")
            yield Label("[dim]Click on the image to get pixel color[/]")

            # Load and display image
            self.pil_image = PILImage.open(self.image_path)

            # Convert to RGB for consistent color picking
            if self.pil_image.mode not in ("RGB", "RGBA"):
                self.pil_image = self.pil_image.convert("RGB")

            # Resize if too large
            width, height = self.pil_image.size
            max_width, max_height = 800, 400
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                new_size = (int(width * scale), int(height * scale))
                self.pil_image = self.pil_image.resize(
                    new_size, PILImage.Resampling.LANCZOS
                )

            yield Image(self.pil_image, id="test-image")
            yield Static(
                f"Image: {width}x{height} pixels\nClick on the image...", id="info"
            )

    def on_click(self, event: events.Click) -> None:
        """Handle click events."""
        # Get the Image widget
        try:
            image_widget = self.query_one("#test-image", Image)
            info = self.query_one("#info", Static)

            # Check if click was on the image widget
            clicked_widget = self.get_widget_at(event.screen_offset)[0]
            if clicked_widget != image_widget:
                info.update("Click was outside image widget")
                return

            # Get widget-relative coordinates
            widget_region = image_widget.region
            relative_x = event.screen_x - widget_region.x
            relative_y = event.screen_y - widget_region.y

            # Get widget size in cells
            widget_width = widget_region.width
            widget_height = widget_region.height

            # Get actual image size in pixels
            img_width, img_height = self.pil_image.size

            # Map cell coordinates to pixel coordinates
            pixel_x = int((relative_x / widget_width) * img_width)
            pixel_y = int((relative_y / widget_height) * img_height)

            # Clamp to image bounds
            pixel_x = max(0, min(pixel_x, img_width - 1))
            pixel_y = max(0, min(pixel_y, img_height - 1))

            # Get pixel color
            pixel_color = self.pil_image.getpixel((pixel_x, pixel_y))

            # Format color based on image mode
            if isinstance(pixel_color, int):
                # Grayscale
                r = g = b = pixel_color
                color_str = f"Gray: {pixel_color}"
            elif len(pixel_color) == 3:
                # RGB
                r, g, b = pixel_color
                color_str = f"RGB({r}, {g}, {b})"
            elif len(pixel_color) == 4:
                # RGBA
                r, g, b, a = pixel_color
                color_str = f"RGBA({r}, {g}, {b}, {a})"
            else:
                r = g = b = 0
                color_str = str(pixel_color)

            hex_str = f"#{r:02x}{g:02x}{b:02x}"

            info.update(
                f"[bold]Clicked:[/] Cell({relative_x}, {relative_y}) → "
                f"Pixel({pixel_x}, {pixel_y})\n"
                f"[bold]Color:[/] {color_str}\n"
                f"[bold]Hex:[/] {hex_str}"
            )

        except Exception as e:
            info = self.query_one("#info", Static)
            info.update(f"[red]Error: {e}[/]")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python test_image_click.py <path_to_image>")
        print("\nExample:")
        print("  pixi run uv run python test_image_click.py data/processed/hawaii.png")
        sys.exit(1)

    image_path = Path(sys.argv[1])
    if not image_path.exists():
        print(f"Error: Image not found: {image_path}")
        sys.exit(1)

    app = ImageClickTestApp(image_path)
    app.run()
