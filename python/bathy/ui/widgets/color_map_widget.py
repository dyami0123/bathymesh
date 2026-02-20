"""Widget for editing color map configurations."""

import logging
from collections import OrderedDict
from typing import Any, Union

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, DataTable, Input, Label, Static

logger = logging.getLogger(__name__)


class ColorMapWidget(Vertical):
    """Widget for editing color-to-height value mappings.

    Displays a table of colors with their associated height values and fuzziness.
    Allows adding, editing, and removing color entries.
    """

    def __init__(self, color_map: OrderedDict, **kwargs) -> None:
        """Initialize ColorMapWidget.

        Args:
            color_map: Ordered dict of color -> {value, fuzziness}
            **kwargs: Additional arguments for Vertical
        """
        super().__init__(**kwargs)
        self._color_map = OrderedDict(color_map)  # Make a copy
        self._show_add_form = False

    def compose(self) -> ComposeResult:
        """Compose the widget UI."""
        yield Label("Color Map Configuration", classes="section-heading")
        yield Label(
            "[dim]Colors are mapped to height values with fuzziness (Delta E). Press Enter to edit selected entry.[/]"
        )

        # Color table
        table = DataTable(id="color-table")
        yield table

        # Button bar
        with Horizontal(classes="button-bar"):
            yield Button("➕ Add Entry", id="add-button", classes="action-button")
            yield Button("✏️ Edit Entry", id="edit-button", classes="action-button")
            yield Button("🗑️ Delete Entry", id="delete-button", classes="action-button")

        # Add form (initially hidden)
        with Container(id="add-form") as form:
            form.display = False
            yield Label("[bold]Add New Color Entry[/]")
            with Horizontal():
                yield Label("Color (hex):")
                yield Input(placeholder="#FF0000", id="color-input")
            with Horizontal():
                yield Label("Height Value:")
                yield Input(placeholder="10.0", id="value-input")
            with Horizontal():
                yield Label("Fuzziness:")
                yield Input(placeholder="5.0", id="fuzziness-input")
            with Horizontal():
                yield Button("Add", id="confirm-add-button", variant="primary")
                yield Button("Cancel", id="cancel-add-button")

    def on_mount(self) -> None:
        """Initialize table after mounting."""
        table = self.query_one("#color-table", DataTable)
        table.cursor_type = "row"
        table.add_columns("Color", "Hex", "Height Value", "Fuzziness")
        self._refresh_table()

    def on_key(self, event) -> None:
        """Handle key presses for table editing."""
        # Check if a DataTable has focus
        try:
            table = self.query_one("#color-table", DataTable)
            if table.has_focus and event.key == "enter":
                # Edit selected entry on Enter
                if table.cursor_row:
                    self._edit_selected_entry()
                    event.prevent_default()
        except Exception:
            pass  # Table might not be mounted yet

    def _refresh_table(self) -> None:
        """Refresh the color table display."""
        table = self.query_one("#color-table", DataTable)
        table.clear()

        for color_hex, props in self._color_map.items():
            value = props.get("value", 0.0)
            fuzziness = props.get("fuzziness", 5.0)

            # Show color swatch (using background color)
            color_display = f"[{color_hex} on {color_hex}]  ███  [/]"

            table.add_row(
                color_display,
                color_hex,
                f"{value:.2f}",
                f"{fuzziness:.2f}",
                key=color_hex,
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "add-button":
            self._show_add_form_ui()
        elif event.button.id == "edit-button":
            self._edit_selected_entry()
        elif event.button.id == "delete-button":
            self._delete_selected_entry()
        elif event.button.id == "confirm-add-button":
            self._add_entry()
        elif event.button.id == "cancel-add-button":
            self._hide_add_form_ui()

    def _show_add_form_ui(self) -> None:
        """Show the add entry form."""
        form = self.query_one("#add-form", Container)
        form.display = True
        self.query_one("#color-input", Input).focus()

    def _hide_add_form_ui(self) -> None:
        """Hide the add entry form."""
        form = self.query_one("#add-form", Container)
        form.display = False
        # Clear inputs
        self.query_one("#color-input", Input).value = ""
        self.query_one("#value-input", Input).value = ""
        self.query_one("#fuzziness-input", Input).value = ""

    def _add_entry(self) -> None:
        """Add a new color map entry."""
        color_input = self.query_one("#color-input", Input)
        value_input = self.query_one("#value-input", Input)
        fuzziness_input = self.query_one("#fuzziness-input", Input)

        color_hex = color_input.value.strip()

        # Validate hex color
        if not color_hex.startswith("#") or len(color_hex) != 7:
            logger.error("Invalid color format. Use #RRGGBB")
            return

        try:
            value = float(value_input.value)
            fuzziness = float(fuzziness_input.value)
        except ValueError as e:
            logger.error(f"Invalid numeric value: {e}")
            return

        # Add to color map
        self._color_map[color_hex] = {"value": value, "fuzziness": fuzziness}

        self._refresh_table()
        self._hide_add_form_ui()
        logger.info(
            f"Added color entry: {color_hex} -> {value} (fuzziness: {fuzziness})"
        )

    def _edit_selected_entry(self) -> None:
        """Edit the selected color entry."""
        table = self.query_one("#color-table", DataTable)

        if not table.cursor_row:
            logger.warning("No entry selected")
            return

        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key

        # Get the actual color hex value from row_key
        color_hex = row_key.value if hasattr(row_key, "value") else str(row_key)

        if color_hex not in self._color_map:
            logger.warning(f"Color {color_hex} not found in color map")
            return

        props = self._color_map[color_hex]

        # Pre-fill form with current values
        self.query_one("#color-input", Input).value = color_hex
        self.query_one("#value-input", Input).value = str(props["value"])
        self.query_one("#fuzziness-input", Input).value = str(props["fuzziness"])

        # Remove old entry (will be re-added when form is submitted)
        del self._color_map[color_hex]
        self._refresh_table()

        self._show_add_form_ui()

    def _delete_selected_entry(self) -> None:
        """Delete the selected color entry."""
        table = self.query_one("#color-table", DataTable)

        if not table.cursor_row:
            logger.warning("No entry selected")
            return

        row_key = table.coordinate_to_cell_key(table.cursor_coordinate).row_key

        # Get the actual color hex value from row_key
        color_hex = row_key.value if hasattr(row_key, "value") else str(row_key)

        if color_hex in self._color_map:
            del self._color_map[color_hex]
            self._refresh_table()
            logger.info(f"Deleted color entry: {color_hex}")

    def get_color_map(self) -> OrderedDict:
        """Get the current color map.

        Returns:
            OrderedDict of color hex codes to value/fuzziness dicts
        """
        return OrderedDict(self._color_map)
