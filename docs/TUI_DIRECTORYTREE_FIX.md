# DirectoryTree Performance Fix

## Problem
Opening a project had a 4-5 second freeze between clicking "Open Project" and the UI appearing. This was caused by the `DirectoryTree` widget scanning the entire directory tree during composition, which blocks the UI thread.

## Solution
Removed `DirectoryTree` from `WorkflowImageWidget` and replaced it with a simple text `Input` field for file paths.

## Changes Made

### `python/bathy/ui/widgets/workflow_image_widget.py`
- **Removed**: `DirectoryTree` import and widget
- **Added**: `Input` widget for file path entry (id: `file-path-input`)
- **Added**: "Browse..." button (id: `browse-btn`) for future file browser modal
- **Removed**: `on_directory_tree_file_selected()` handler
- **Added**: `on_input_changed()` handler for manual path input
- **Updated**: `on_mount()` to populate file path input instead of DirectoryTree
- **Updated**: `_use_current_source()` to populate file path input
- **Added**: CSS styling for Button widget

### Files That Did NOT Need Changes
- `python/bathy/ui/widgets/workflow_mesh_widget.py` - Never used DirectoryTree

## Testing Required

### Manual Testing
1. **Launch TUI**: `pixi run bathy --debug`
2. **Click "Open Project"** - Should take <1 second (not 4-5 seconds)
3. **Go to "Image → Heightmap" tab** - Should display file input field
4. **Type a file path manually** - Should update selection
5. **Click "Use Project Source Image"** - Should populate input with project's source image
6. **Click "Process"** - Modal should appear immediately, processing should work

### Expected Behavior After Fix
- Fast project loading (<1 second instead of 4-5 seconds)
- Visible workflow UI with file input, config fields, and buttons
- Working file selection via text input
- "Use Project Source Image" button works
- Modal appears immediately when clicking "Process"

### Known Limitations
- **No file browser yet**: The "Browse..." button is a placeholder
- **Manual path entry only**: Users must type full file paths
- **Future enhancement**: Add a proper file browser modal that loads on-demand

## Performance Impact
- **Before**: 4-5 second delay (DirectoryTree scanning filesystem during composition)
- **After**: <1 second (simple Input field, no filesystem scanning)

## Architecture Notes
DirectoryTree is expensive because it:
1. Scans the entire directory tree recursively during composition
2. Blocks the main UI thread while scanning
3. Loads all file/folder metadata upfront

The fix avoids this by:
1. Using a lightweight Input field instead
2. Only validating paths when user submits
3. No upfront filesystem scanning

## Future Improvements
1. Add a file browser modal that:
   - Opens on-demand when "Browse..." is clicked
   - Uses lazy-loading DirectoryTree (load subdirs only when expanded)
   - Doesn't block the main project loading flow
2. Add file path validation with visual feedback
3. Add autocomplete for file paths
4. Add recent files history
