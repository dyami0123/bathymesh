"""Image preview widgets with lazy loading, simple and interactive variants.

This module provides three widget classes:
- BaseImagePreview: Shared functionality for image loading and display
- SimpleImagePreview: Basic image preview without interaction
- InteractiveImagePreview: Image preview with color picking and zoom preview
"""

import logging
from pathlib import Path
from typing import Union

from PIL import Image as PILImage, ImageDraw
from rich.text import Text
from textual import events, work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.widgets import Button, Label, Static
from textual.worker import get_current_worker
from textual_image.widget import Image

logger = logging.getLogger(__name__)


class BaseImagePreview(Vertical):
    """Base class for image preview widgets with shared loading functionality.

    Features:
    - Lazy loading: Image only loads when explicitly requested
    - Size limiting: Large images are automatically scaled to fit UI
    - Error handling: Displays error message if image fails to load

    Subclasses should override compose_preview_ui() to customize the UI.
    """

    # Maximum dimensions for image preview (in terminal cells)
    MAX_WIDTH = 80  # cells
    MAX_HEIGHT = 40  # cells

    def __init__(self, **kwargs) -> None:
        """Initialize BaseImagePreview.

        Args:
            **kwargs: Additional arguments for Vertical
        """
        super().__init__(**kwargs)
        self._image_path: Union[Path, None] = None
        self._is_loaded = False
        self._pil_image: Union[PILImage.Image, None] = None
        self._scaled_image: Union[PILImage.Image, None] = None

    def compose(self) -> ComposeResult:
        """Compose the base widget UI."""
        with Container(id="preview-container"):
            yield Label("Image Preview", classes="section-heading")

            # Let subclasses add their own UI elements
            yield from self.compose_preview_ui()

    def compose_preview_ui(self) -> ComposeResult:
        """Compose subclass-specific UI elements.

        Override this method in subclasses to customize the preview UI.
        """
        # Default implementation - basic preview
        yield Static("Click 'Load Preview' to display image", id="preview-placeholder")
        yield Image(id="preview-image")
        yield Button("🖼️  Load Preview", id="load-preview-button")
        yield Static("", id="preview-status")

    def set_image_path(self, path: Union[Path, str, None]) -> None:
        """Set the image path and reset the preview.

        Args:
            path: Path to image file, or None to clear
        """
        if path is None:
            self._image_path = None
            self._is_loaded = False
            self._pil_image = None
            self._scaled_image = None
            self._show_placeholder()
            return

        self._image_path = Path(path) if isinstance(path, str) else path
        self._is_loaded = False
        self._pil_image = None
        self._scaled_image = None
        self._show_placeholder()

        # Enable load button if path is valid
        try:
            load_button = self.query_one("#load-preview-button", Button)
            load_button.disabled = not (self._image_path and self._image_path.exists())
        except Exception as e:
            logger.debug(f"Could not update load button: {e}")

    def _show_placeholder(self) -> None:
        """Show the placeholder and hide the image."""
        try:
            placeholder = self.query_one("#preview-placeholder", Static)
            placeholder.display = True

            image_widget = self.query_one("#preview-image", Image)
            image_widget.display = False

            status = self.query_one("#preview-status", Static)
            status.update("")
        except Exception as e:
            logger.debug(f"Could not update placeholder: {e}")

    def _show_image(self) -> None:
        """Show the image and hide the placeholder."""
        try:
            placeholder = self.query_one("#preview-placeholder", Static)
            placeholder.display = False

            image_widget = self.query_one("#preview-image", Image)
            image_widget.display = True
        except Exception as e:
            logger.debug(f"Could not show image: {e}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press to load preview."""
        if event.button.id == "load-preview-button":
            if self._image_path and self._image_path.exists():
                self._load_preview(self._image_path)

    @work(exclusive=True, thread=True)
    def _load_preview(self, image_path: Path) -> None:
        """Load and display the image preview.

        Args:
            image_path: Path to image file
        """
        worker = get_current_worker()

        try:
            # Update status
            def set_loading():
                status = self.query_one("#preview-status", Static)
                status.update("[dim]Loading preview...[/]")

            self.app.call_from_thread(set_loading)

            if worker.is_cancelled:
                return

            # Load image with PIL (store original for accuracy)
            original_image = PILImage.open(image_path)

            # Convert to RGB if needed
            if original_image.mode not in ("RGB", "RGBA"):
                original_image = original_image.convert("RGB")

            # Calculate scaled dimensions
            width, height = original_image.size
            cell_width = width // 10
            cell_height = height // 20

            # Scale down if necessary
            scaled_image = original_image
            if cell_width > self.MAX_WIDTH or cell_height > self.MAX_HEIGHT:
                scale_x = (
                    self.MAX_WIDTH / cell_width if cell_width > self.MAX_WIDTH else 1.0
                )
                scale_y = (
                    self.MAX_HEIGHT / cell_height
                    if cell_height > self.MAX_HEIGHT
                    else 1.0
                )
                scale = min(scale_x, scale_y)

                new_width = int(width * scale)
                new_height = int(height * scale)
                scaled_image = original_image.resize(
                    (new_width, new_height), PILImage.Resampling.LANCZOS
                )

                logger.info(
                    f"Scaled image from {width}x{height} to {new_width}x{new_height}"
                )

            if worker.is_cancelled:
                return

            # Store both images
            self._pil_image = original_image
            self._scaled_image = scaled_image

            # Update the image widget
            def update_image():
                try:
                    image_widget = self.query_one("#preview-image", Image)
                    image_widget.image = scaled_image

                    self._show_image()
                    self._is_loaded = True

                    # Update status with image dimensions
                    status = self.query_one("#preview-status", Static)
                    if scaled_image.size != original_image.size:
                        status.update(
                            f"[dim]{scaled_image.size[0]}x{scaled_image.size[1]} pixels (display) | "
                            f"{original_image.size[0]}x{original_image.size[1]} pixels (original)[/]"
                        )
                    else:
                        status.update(
                            f"[dim]{original_image.size[0]}x{original_image.size[1]} pixels[/]"
                        )

                    # Disable load button
                    load_button = self.query_one("#load-preview-button", Button)
                    load_button.disabled = True

                    # Call subclass hook for post-load actions
                    self._on_image_loaded()

                except Exception as e:
                    logger.error(f"Failed to update image widget: {e}")
                    status = self.query_one("#preview-status", Static)
                    status.update(f"[red]Error displaying image: {e}[/]")

            self.app.call_from_thread(update_image)
            logger.info(f"Loaded preview: {image_path.name}")

        except Exception as e:
            if not worker.is_cancelled:
                logger.error(f"Failed to load preview: {e}", exc_info=True)

                def show_error():
                    status = self.query_one("#preview-status", Static)
                    status.update(f"[red]Error loading image: {e}[/]")

                self.app.call_from_thread(show_error)

    def _on_image_loaded(self) -> None:
        """Hook called after image is successfully loaded.

        Subclasses can override this to perform actions after loading.
        """
        pass


class SimpleImagePreview(BaseImagePreview):
    """Simple image preview without interaction features.

    Just displays the image with basic loading functionality.
    """

    # Inherits all functionality from BaseImagePreview
    # No additional features needed
    pass


class InteractiveImagePreview(BaseImagePreview):
    """Interactive image preview with color picking and zoom preview.

    Features:
    - Click to pick pixel color (RGB/Hex display)
    - Mouse hover shows zoomed preview of area under cursor
    - Real-time zoom updates as mouse moves
    """

    # Zoom preview settings
    ZOOM_SIZE = 32  # Size of zoom preview in pixels
    ZOOM_FACTOR = 4  # Magnification factor

    def compose_preview_ui(self) -> ComposeResult:
        """Compose interactive UI with color picking and zoom."""
        yield Label(
            "[dim]Click to pick color, hover to see zoom preview[/]", id="preview-hint"
        )

        yield Static("Click 'Load Preview' to display image", id="preview-placeholder")
        yield Image(id="preview-image")
        yield Button("🖼️  Load Preview", id="load-preview-button")
        yield Static("", id="preview-status")

        # Color info display (hidden initially)
        yield Static("", id="preview-color-info")

        # Zoom preview (hidden initially)
        with Container(id="preview-zoom-container"):
            yield Label("Zoom Preview", classes="section-heading")
            yield Static("", id="preview-zoom-display")

    def _on_image_loaded(self) -> None:
        """Show zoom container after image loads."""
        try:
            zoom_container = self.query_one("#preview-zoom-container", Container)
            zoom_container.display = True
        except Exception as e:
            logger.debug(f"Could not show zoom container: {e}")

    def _show_placeholder(self) -> None:
        """Override to also hide interactive elements."""
        super()._show_placeholder()
        try:
            zoom_container = self.query_one("#preview-zoom-container", Container)
            zoom_container.display = False

            color_info = self.query_one("#preview-color-info", Static)
            color_info.update("")
        except Exception as e:
            logger.debug(f"Could not hide interactive elements: {e}")

    def on_click(self, event: events.Click) -> None:
        """Handle click events for color picking."""
        if not self._is_loaded or not self._pil_image or not self._scaled_image:
            return

        try:
            image_widget = self.query_one("#preview-image", Image)

            # Check if click was on image
            clicked_widget = self.get_widget_at(event.screen_offset)[0]
            if clicked_widget != image_widget:
                return

            # Get pixel coordinates and color
            pixel_x, pixel_y, pixel_color = self._get_pixel_at_position(
                event.screen_x, event.screen_y, image_widget
            )

            if pixel_color is None:
                return

            # Format color display
            color_str, hex_str = self._format_color(pixel_color)

            # Update color info
            color_info = self.query_one("#preview-color-info", Static)
            color_info.update(
                f"[bold]Pixel:[/] ({pixel_x}, {pixel_y}) | "
                f"[bold]Color:[/] {color_str} | [bold]Hex:[/] {hex_str}"
            )

            logger.debug(
                f"Color picked: ({pixel_x}, {pixel_y}) = {color_str} ({hex_str})"
            )

        except Exception as e:
            logger.error(f"Error picking pixel color: {e}", exc_info=True)

    def on_mouse_move(self, event: events.MouseMove) -> None:
        """Handle mouse move to update zoom preview."""
        if not self._is_loaded or not self._pil_image or not self._scaled_image:
            return

        try:
            image_widget = self.query_one("#preview-image", Image)

            # Check if mouse is over image
            widget_at_pos = self.get_widget_at(event.screen_offset)[0]
            if widget_at_pos != image_widget:
                return

            # Get pixel coordinates
            pixel_x, pixel_y, _ = self._get_pixel_at_position(
                event.screen_x, event.screen_y, image_widget
            )

            if pixel_x is None or pixel_y is None:
                return

            # Generate zoom preview
            self._update_zoom_preview(pixel_x, pixel_y)

        except Exception as e:
            logger.debug(f"Error updating zoom preview: {e}")

    def _get_pixel_at_position(
        self, screen_x: int, screen_y: int, image_widget: Image
    ) -> tuple[Union[int, None], Union[int, None], Union[tuple, None]]:
        """Get pixel coordinates and color at screen position.

        Args:
            screen_x: Screen X coordinate
            screen_y: Screen Y coordinate
            image_widget: The image widget

        Returns:
            Tuple of (pixel_x, pixel_y, pixel_color) or (None, None, None)
        """
        try:
            # Get widget-relative coordinates
            widget_region = image_widget.region
            relative_x = screen_x - widget_region.x
            relative_y = screen_y - widget_region.y

            # Get sizes
            widget_width = widget_region.width
            widget_height = widget_region.height
            display_width, display_height = self._scaled_image.size
            original_width, original_height = self._pil_image.size

            # Map to pixel coordinates
            display_pixel_x = int((relative_x / widget_width) * display_width)
            display_pixel_y = int((relative_y / widget_height) * display_height)

            # Clamp to display bounds
            display_pixel_x = max(0, min(display_pixel_x, display_width - 1))
            display_pixel_y = max(0, min(display_pixel_y, display_height - 1))

            # Map to original image for accurate color
            original_pixel_x = int((display_pixel_x / display_width) * original_width)
            original_pixel_y = int((display_pixel_y / display_height) * original_height)

            # Clamp to original bounds
            original_pixel_x = max(0, min(original_pixel_x, original_width - 1))
            original_pixel_y = max(0, min(original_pixel_y, original_height - 1))

            # Get pixel color
            pixel_color = self._pil_image.getpixel((original_pixel_x, original_pixel_y))

            return original_pixel_x, original_pixel_y, pixel_color

        except Exception as e:
            logger.debug(f"Error getting pixel at position: {e}")
            return None, None, None

    def _format_color(self, pixel_color: tuple) -> tuple[str, str]:
        """Format pixel color as RGB string and hex string.

        Args:
            pixel_color: Pixel color tuple from PIL

        Returns:
            Tuple of (color_str, hex_str)
        """
        if isinstance(pixel_color, int):
            # Grayscale
            r = g = b = pixel_color
            color_str = f"Gray({pixel_color})"
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
        return color_str, hex_str

    def _update_zoom_preview(self, center_x: int, center_y: int) -> None:
        """Update the zoom preview display.

        Args:
            center_x: Center X coordinate in original image
            center_y: Center Y coordinate in original image
        """
        try:
            # Extract region around cursor
            half_size = self.ZOOM_SIZE // 2
            left = max(0, center_x - half_size)
            top = max(0, center_y - half_size)
            right = min(self._pil_image.width, center_x + half_size)
            bottom = min(self._pil_image.height, center_y + half_size)

            # Crop region
            zoom_region = self._pil_image.crop((left, top, right, bottom))

            # Scale up for zoom effect
            zoom_width = zoom_region.width * self.ZOOM_FACTOR
            zoom_height = zoom_region.height * self.ZOOM_FACTOR
            zoomed = zoom_region.resize(
                (zoom_width, zoom_height), PILImage.Resampling.NEAREST
            )

            # Draw crosshair at center
            draw = ImageDraw.Draw(zoomed)
            center_zoom_x = (center_x - left) * self.ZOOM_FACTOR
            center_zoom_y = (center_y - top) * self.ZOOM_FACTOR

            # Draw crosshair lines
            crosshair_color = (255, 0, 0)  # Red
            line_length = 10
            draw.line(
                [
                    (center_zoom_x - line_length, center_zoom_y),
                    (center_zoom_x + line_length, center_zoom_y),
                ],
                fill=crosshair_color,
                width=2,
            )
            draw.line(
                [
                    (center_zoom_x, center_zoom_y - line_length),
                    (center_zoom_x, center_zoom_y + line_length),
                ],
                fill=crosshair_color,
                width=2,
            )

            # Create text representation for terminal
            # Use Rich Text with colored blocks
            text_lines = []
            for y in range(0, zoomed.height, 2):  # Step by 2 for half-block chars
                line_parts = []
                for x in range(zoomed.width):
                    if y < zoomed.height:
                        pixel = zoomed.getpixel((x, y))
                        if isinstance(pixel, int):
                            r = g = b = pixel
                        else:
                            r, g, b = pixel[:3]

                        # Use Rich color blocks
                        line_parts.append(f"[on rgb({r},{g},{b})] [/]")

                text_lines.append("".join(line_parts))

            # Update zoom display
            zoom_display = self.query_one("#preview-zoom-display", Static)
            zoom_text = "\n".join(text_lines)
            zoom_display.update(
                f"{zoom_text}\n[dim]Position: ({center_x}, {center_y})[/]"
            )

        except Exception as e:
            logger.debug(f"Error updating zoom preview: {e}")
