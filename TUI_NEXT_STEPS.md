# TUI Development - Next Steps

## Current Status (Session End)

### ✅ Completed (4 commits on feature/tui branch)

1. **Foundation** (commit 5fac14f)
   - Config I/O with YAML serialization
   - Project Manager with CRUD operations
   - Basic TUI app structure

2. **Core Screens** (commit b6d896d)
   - Main menu
   - Project list with DataTable
   - New project dialog with validation
   - Project detail screen

3. **Workflow Screens** (commit 986e390)
   - Image → Heightmap workflow
   - Heightmap → Mesh workflow
   - Async processing with @work decorator
   - Status logging

4. **UX Improvements** (commit feb0aca)
   - Fixed _log() error (Static.render() instead of .renderable)
   - Enter key support in project list
   - Tab-based project detail (Overview, workflows in tabs)
   - 'bathy' command entry point

### 🎯 Next Priority Tasks

#### 1. Loading & Log Handling for Long-Running Tasks (HIGH PRIORITY)

**Current Issues:**
- No visual feedback during long operations (image processing, mesh generation)
- Log output just appends to Static widget, no scrolling
- No progress indication (percentage, spinner, etc.)
- UI appears frozen during @work operations

**Proposed Improvements:**
- Add `LoadingIndicator` widget during processing
- Use `RichLog` widget instead of Static for scrollable log output
- Add progress tracking:
  - For image processing: show stages (load → process → save)
  - For mesh generation: show progress through thresholds/layers
- Disable buttons during processing
- Show elapsed time
- Add cancel button for long operations

**Files to Modify:**
- `python/bathy/ui/screens/workflow_image.py`
- `python/bathy/ui/screens/workflow_mesh.py`

**Implementation Notes:**
- Textual has built-in `LoadingIndicator` widget
- Consider using `ProgressBar` for determinate progress
- May need to modify underlying workflow functions to report progress
- Use `RichLog` for better log display with syntax highlighting

#### 2. Shared Project UI Container with Header Dropdowns (HIGH PRIORITY)

**Current Issues:**
- Each screen is independent
- No consistent project context across screens
- Can't easily switch projects or reload
- No way to reset configs to defaults without manual editing

**Proposed Design:**
- Create a `ProjectContainer` screen/widget that wraps project-related screens
- Header bar with:
  - **Project dropdown**: Switch between projects without going back to list
  - **Actions dropdown**: 
    - Reload project
    - Reset configs to defaults
    - Export project
    - Delete project (with confirmation)
  - **Current project name** always visible
  - **Status indicator** (New, Processing, Ready)
- Footer with:
  - Quick stats (files present, last modified)
  - Keyboard shortcuts

**Implementation:**
- Create new `ProjectContainer` screen
- Refactor project detail, workflow screens to be children
- Move project loading/switching logic to container
- Add dropdown menu widgets (Textual has `OptionList`)

**Files to Create/Modify:**
- NEW: `python/bathy/ui/screens/project_container.py`
- MODIFY: `python/bathy/ui/screens/project_detail.py`
- MODIFY: `python/bathy/ui/screens/workflow_image.py`
- MODIFY: `python/bathy/ui/screens/workflow_mesh.py`
- MODIFY: `python/bathy/ui/app.py`

#### 3. Config DataTable Refactor (MEDIUM PRIORITY)

**Current Issues:**
- Too many Input widgets (verbose, hard to scan)
- No overview of all config values
- Hard to compare with defaults
- Nested configs (HeighmapProcessingConfig, etc.) not clearly grouped

**Proposed Design:**
- Replace Input fields with editable DataTable
- 3 columns: Variable Name | Value | Description
- Only Value column editable
- Tabs for config sections:
  - **Image Processing**: Basic settings, color map
  - **Heightmap Processing**: Buffer, offset, units, thresholds
  - **Contour Extraction**: Polygon area, tolerance, segments
  - **Triangulation**: Interior points, density
  - **Post Processing**: Cleanup options
  - **Mesh Combination**: Merge thresholds
- Color-code rows by data type (int=blue, float=green, bool=yellow)
- Show validation errors inline
- "Reset to Default" button per tab

**Implementation Challenges:**
- DataTable cells not directly editable in Textual (need custom solution)
- Options:
  1. Modal edit dialog when row selected
  2. Inline Input that appears on cell activation
  3. Use `Input` widgets in a scrollable form, just better organized
- Need type conversion and validation
- Handle special cases (list of thresholds, OrderedDict for color map)

**Files to Modify:**
- `python/bathy/ui/screens/workflow_image.py` - Complete refactor
- `python/bathy/ui/screens/workflow_mesh.py` - Complete refactor
- Possibly create new widget: `python/bathy/ui/widgets/config_table.py`

## Architecture Notes for Next Session

### Current Screen Flow
```
Main Menu
├── Open Project → Project List → Project Detail (tabs)
│                                   ├── Overview
│                                   ├── Image → Heightmap (pushes screen)
│                                   └── Heightmap → Mesh (pushes screen)
└── New Project → New Project Dialog → Project Detail
```

### Proposed Screen Flow (after Task #2)
```
Main Menu
├── Open Project → Project List → ProjectContainer
│                                   ├── Header (project switcher, actions)
│                                   ├── Tabbed Content
│                                   │   ├── Overview
│                                   │   ├── Image → Heightmap
│                                   │   └── Heightmap → Mesh
│                                   └── Footer (stats, shortcuts)
└── New Project → New Project Dialog → ProjectContainer
```

### Key Classes

**Current:**
- `BathymeshApp` - Main app, screen manager
- `ProjectManager` - CRUD operations
- `Project` - Single project state
- Individual screens (6 total)

**Proposed Addition:**
- `ProjectContainer` - Wrapper for all project-related views
  - Holds current project reference
  - Manages project switching
  - Provides reset/reload actions
  - Persistent header/footer across tabs

## Testing Strategy

Before starting each task:
1. Test current functionality works
2. Create feature branch if desired
3. Make incremental changes
4. Test after each logical unit
5. Use `pixi run bathy` or `timeout 5 pixi run bathy` for smoke tests

## Current Branch State
- **Branch**: feature/tui
- **Commits**: 4 (all clean, well-documented)
- **Status**: Working, ready for next phase
- **Entry point**: `pixi run bathy` or `bathy` after install

## Notes
- LSP errors about "App[Unknown]" attributes are false positives (type checking issue)
- Test projects exist in `data/projects/` (test-europa, test-hawaii, test-new-project)
- All workflows functional but need UX polish
- No breaking bugs, just UX improvements needed
