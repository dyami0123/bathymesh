# Bathymesh TUI

A terminal-based user interface for bathymesh 3D mesh generation.

## Quick Start

Run the TUI:
```bash
# Use default projects directory (~/bathymesh_projects)
pixi run uv run python -m bathy

# Or specify custom projects directory
pixi run uv run python -m bathy /path/to/projects
```

## Features

### Project Management
- Create new projects with descriptions
- List and open existing projects
- Project metadata tracking (creation date, status, etc.)

### Image → Heightmap Workflow
- Load source images (PNG, JPG, etc.)
- Configure image processing parameters
- Preview file information before processing
- Generate heightmaps with real-time progress logs
- Save heightmaps to project directory

### Heightmap → Mesh Workflow
- Load heightmap files (.npy)
- Configure mesh generation parameters
- Preview heightmap statistics
- Generate 3D meshes (STL format)
- Save meshes to project directory

### Configuration
- Edit all processing parameters via interactive tables
- Configurations saved per project
- Automatically load previous settings

## Architecture

### File Structure
```
python/bathy/ui/
├── app.py                          # Main BathymeshApp
├── screens/
│   ├── main_menu_screen.py         # Project selection screen
│   ├── project_screen.py           # Main project screen with tabs
│   └── new_project_dialog.py       # Dialog for creating projects
├── widgets/
│   ├── overview_widget.py          # Project overview tab
│   ├── image_workflow_widget.py    # Image→Heightmap workflow
│   ├── mesh_workflow_widget.py     # Heightmap→Mesh workflow
│   ├── processing_modal.py         # Modal with streaming logs
│   └── config_table.py             # DataTable for config editing
└── styles/
    └── app.tcss                    # Global styles
```

### Key Design Decisions

1. **Lazy Loading**: File data is only loaded when explicitly requested (Preview/Process buttons)
2. **Worker Pattern**: All I/O operations run in background workers using `@work` decorator
3. **Modal Feedback**: Long-running operations show progress in modal with streaming logs
4. **Project-Centric**: All data organized in project directories with YAML metadata

## Keyboard Shortcuts

### Main Menu
- `n` - New project
- `q` - Quit application
- `Enter` - Open selected project

### Project Screen
- `Escape` - Back to projects
- Tab keys to navigate between workflow tabs

## Project Structure

Each project creates this directory structure:
```
project-name/
├── project.yaml           # Project metadata
├── image_config.yaml      # Image processing configuration
├── mesh_config.yaml       # Mesh generation configuration
├── source/                # Source images
├── heightmap/             # Generated heightmaps
└── meshes/                # Generated 3D meshes
```

## Configuration Parameters

### Image Processing
- **Basic**: Resolution control, region of interest
- **NaN Filling**: Parameters for filling missing data
- **Color Mapping**: Color-to-height value mapping

### Mesh Generation
- **Heightmap Processing**: Buffer, offset, thresholds, layers
- **Mesh Units**: X/Y/Z scaling factors
- **Contour Extraction**: Polygon filtering, simplification
- **Triangulation**: Interior points, density
- **Post-Processing**: Cleaning, simplification, optimization

## Development

### Testing Components
```bash
# Test all component imports
pixi run uv run python test_tui.py

# Run the TUI in development
pixi run uv run python -m bathy /tmp/test_projects
```

### Adding New Widgets
1. Create widget in `python/bathy/ui/widgets/`
2. Export in `widgets/__init__.py`
3. Use in screens as needed

### Adding New Screens
1. Create screen in `python/bathy/ui/screens/`
2. Export in `screens/__init__.py`
3. Push/pop screen from app

## Troubleshooting

### TUI won't start
- Ensure terminal supports colors and Unicode
- Check that textual is installed: `pixi run uv run pip list | grep textual`

### Can't see file previews
- Check file paths are correct
- Ensure files have proper permissions
- Check logs in `[projects_root]/bathymesh_tui.log`

### Processing fails
- Check file formats are supported
- Review configuration parameters
- Check disk space in project directory
- Review error messages in processing modal

## Logging

Logs are written to `bathymesh_tui.log` in the projects root directory.

View logs in real-time:
```bash
tail -f ~/bathymesh_projects/bathymesh_tui.log
```
