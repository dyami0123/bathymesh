"""Main menu screen for project selection."""

import logging

from textual import work
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ListItem, ListView

from bathy.project_manager import Project, ProjectInfo
from bathy.ui.screens.new_project_dialog import NewProjectDialog
from bathy.ui.screens.project_screen import ProjectScreen

logger = logging.getLogger(__name__)


class MainMenuScreen(Screen):
    """Main menu screen for project selection.

    Lists all existing projects and provides options to:
    - Open an existing project
    - Create a new project
    - Exit the application
    """

    BINDINGS = [
        ("n", "new_project", "New Project"),
        ("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        """Compose the screen UI."""
        yield Header()

        with Container(id="menu-container"):
            yield Label("🌊 BATHYMESH", classes="section-heading", id="title")
            yield Label("[dim]3D Mesh Generation from Maps & Images[/]", id="subtitle")

            yield ListView(id="projects-list")

            with Container(id="button-container"):
                yield Button("📂 Open Project", id="open-button", variant="primary")
                yield Button("➕ New Project", id="new-button")
                yield Button("❌ Exit", id="exit-button")

        yield Footer()

    def on_mount(self) -> None:
        """Initialize screen after mounting."""
        self._load_projects()

    @work(exclusive=True)
    async def _load_projects(self) -> None:
        """Load project list in worker thread."""
        try:
            from bathy.ui.app import BathymeshApp

            app = self.app
            if not isinstance(app, BathymeshApp):
                logger.error("Invalid app context")
                return

            # Get projects
            projects = app.project_manager.list_projects()

            # Update UI
            def update_list():
                projects_list = self.query_one("#projects-list", ListView)
                projects_list.clear()

                if not projects:
                    projects_list.append(ListItem(Label("[dim]No projects found[/]")))
                else:
                    for proj_info in projects:
                        status_emoji = {
                            "none": "📁",
                            "image_loaded": "🖼️",
                            "heightmap_generated": "📊",
                            "mesh_generated": "🗻",
                        }.get(proj_info.status, "📁")

                        label = f"{status_emoji} [bold]{proj_info.name}[/]"
                        if proj_info.description:
                            label += f"\n  [dim]{proj_info.description}[/]"

                        projects_list.append(
                            ListItem(Label(label), name=proj_info.name)
                        )

            update_list()
            logger.info(f"Loaded {len(projects)} projects")

        except Exception as e:
            logger.error(f"Failed to load projects: {e}", exc_info=True)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press."""
        if event.button.id == "open-button":
            self._open_selected_project()
        elif event.button.id == "new-button":
            self.action_new_project()
        elif event.button.id == "exit-button":
            self.action_quit()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle project selection in list."""
        self._open_selected_project()

    def _open_selected_project(self) -> None:
        """Open the selected project."""
        projects_list = self.query_one("#projects-list", ListView)

        if projects_list.index is None:
            logger.info("No Index")
            return

        selected_item = projects_list.children[projects_list.index]
        if not hasattr(selected_item, "name") or not selected_item.name:
            return

        project_name = selected_item.name
        self._load_and_open_project(project_name)

    @work(exclusive=True)
    async def _load_and_open_project(self, project_name: str) -> None:
        """Load project and open project screen.

        Args:
            project_name: Name of project to load
        """
        try:
            from bathy.ui.app import BathymeshApp

            app = self.app
            if not isinstance(app, BathymeshApp):
                logger.error("Invalid app context")
                return

            # Load project
            project = app.project_manager.load_project(project_name)
            logger.info(f"Loaded project: {project_name}")

            # Update app state and push screen
            def open_screen():
                app.current_project = project
                self.app.push_screen(ProjectScreen(project))

            open_screen()

        except Exception as e:
            logger.error(f"Failed to load project {project_name}: {e}", exc_info=True)

    def action_new_project(self) -> None:
        """Show new project dialog."""

        def handle_result(project: Project | None) -> None:
            if project:
                logger.info(f"Created new project: {project.metadata.name}")
                # Reload project list
                self._load_projects()
                # Open the new project
                from bathy.ui.app import BathymeshApp

                app = self.app
                if isinstance(app, BathymeshApp):
                    app.current_project = project
                    self.app.push_screen(ProjectScreen(project))

        self.app.push_screen(NewProjectDialog(), handle_result)

    def action_quit(self) -> None:
        """Exit application."""
        self.app.exit()
