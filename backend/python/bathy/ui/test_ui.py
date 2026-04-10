from time import monotonic

from textual.app import App, ComposeResult
from textual.widgets import Footer, Header
from textual.containers import HorizontalGroup, VerticalScroll, ScrollableContainer
from textual.widgets import Button, Digits, Footer, Header
from textual import on
from textual.widget import Widget
from textual.content import Content
from textual.reactive import reactive
from textual.app import App,ComposeResult,RenderResult
from rich_pixels import Pixels
from textual import events
from copy import copy
from PIL import Image


image_path = "/home/dyami/Documents/git/bathymesh/data/raw/europa.jpg"

img = Image.open(image_path)

class ImageWidget(Widget):
    
    scale_factor: float = 1.
    base_resolution: tuple[int,int] = (0,0)
    pixels = Pixels.from_image(copy(img))
    
    
    def on_mount(self) -> None:
        """Event handler called when widget is added to the app."""
        
        self.base_resolution = img.size
        self.set_interval(1 / 5, self.update_pixels)
        self.auto_refresh = 1/30

    def update_pixels(self) -> None:
        """Method to update the time to the current time."""
        resolution = (
                int(self.base_resolution[0] * self.scale_factor),
                int(self.base_resolution[1] * self.scale_factor),
            )
        print("UPDATING PIXELS", self.scale_factor, resolution)
        self.pixels = Pixels.from_image(
            copy(img),
            resize=resolution,
        )
        
    # def watch_scale_factor()

    # def watch_time(self, time: float) -> None:
    #     """Called when the time attribute changes."""
    #     minutes, seconds = divmod(time, 60)
    #     hours, minutes = divmod(minutes, 60)
    #     self.update(f"{hours:02,.0f}:{minutes:02.0f}:{seconds:05.2f}")

    def render(self) -> RenderResult:
        print("RENDERING")
        return self.pixels
    
    
    @on(events.MouseScrollUp)
    def zoom_in(self, event: events.MouseScrollUp) -> None:
        print("EVENT")
        self.scale_factor *= 1.01
        
    @on(events.MouseScrollDown)
    def zoom_out(self, event: events.MouseScrollDown) -> None:
        print("EVENT")
        self.scale_factor *= 0.99
        
        

class BathymeshApp(App):
    """A Textual app to manage stopwatches."""

    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "add_stopwatch", "Add"),
        ("r", "remove_stopwatch", "Remove"),
        ]
    CSS_PATH = "stopwatch03.tcss"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header(show_clock=False)
        yield Footer()
        yield VerticalScroll(ImageWidget())



if __name__ == "__main__":
    app = BathymeshApp()
    app.run()