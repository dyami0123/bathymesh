# TUI Architecture Changes - Modal Loading & Widget-Based Workflows

## Date: 2026-01-20

## Problems Solved

### 1. Modal Not Showing Until Processing Completes
**Root Cause**: The `@work` decorator runs code in a worker thread, but the modal was being pushed from within the worker thread. This caused the modal push to be queued but not rendered because the worker thread was immediately blocking on the actual processing work.

**Solution**: 
- Separate modal creation from work execution
- Push modal on main thread BEFORE starting worker
- Use `call_from_thread()` for all modal updates from within worker thread

### 2. Workflows as Separate Screens
**Root Cause**: Workflows were implemented as separate `Screen` classes that were pushed onto the navigation stack, making the UI feel disconnected and harder to navigate.

**Solution**:
- Convert workflows from `Screen` to `Widget` classes
- Embed workflow widgets directly in `ProjectDetailScreen` tabs
- Remove screen navigation for workflows

## Architecture Changes

### Old Architecture (Broken)
```
App
├── ProjectDetailScreen (has tabs)
│   └── Tab "Image → Heightmap" 
│       └── on_click: push_screen("workflow_image")  # Pushes new screen
│           └── WorkflowImageScreen (separate screen)
│               └── @work _process_image()
│                   └── push_screen(modal)  # WRONG! From worker thread
```

### New Architecture (Fixed)
```
App
├── ProjectDetailScreen (has tabs)
│   ├── Tab "Overview" → OverviewWidget
│   ├── Tab "Image → Heightmap" → WorkflowImageWidget (embedded widget)
│   │   └── on_button_pressed("process")
│   │       ├── push_screen(modal)  # RIGHT! On main thread
│   │       └── @work _do_process()
│   │           └── modal.call_from_thread(update_status, ...)  # Safe
│   └── Tab "Heightmap → Mesh" → WorkflowMeshWidget (embedded widget)
└── ProcessingModal (true modal dialog with dimmed background)
```

## Files Changed

### New Files Created
- `python/bathy/ui/widgets/workflow_image_widget.py` - Image→Heightmap workflow as widget
- `python/bathy/ui/widgets/workflow_mesh_widget.py` - Heightmap→Mesh workflow as widget
- `python/bathy/ui/widgets/__init__.py` - Export workflow widgets

### Files Modified
- `python/bathy/ui/screens/project_detail.py` - Embed widgets in tabs instead of pushing screens
- `python/bathy/ui/app.py` - Remove workflow screen registrations
- `python/bathy/ui/screens/processing_modal.py` - Already implemented correctly

### Files Deprecated
- `python/bathy/ui/screens/workflow_image.py.deprecated` - Old screen-based implementation
- `python/bathy/ui/screens/workflow_mesh.py.deprecated` - Old screen-based implementation

## Key Implementation Details

### Modal Pattern (Correct)
```python
def _start_processing(self) -> None:
    """Start processing - runs on main thread."""
    # Validate inputs
    if not self.selected_file:
        return
    
    # Create and push modal BEFORE starting work
    modal = ProcessingModal(
        title="🖼️  Processing",
        status="Starting..."
    )
    self.app.push_screen(modal)  # Main thread - renders immediately
    
    # Start work in background
    self._do_process_image(modal)

@work(exclusive=True)
async def _do_process_image(self, modal: ProcessingModal) -> None:
    """Actual processing - runs in worker thread."""
    try:
        # Update modal from worker thread
        modal.call_from_thread(modal.update_status, "Processing...")
        
        # Do the actual work
        result = process_image(...)
        
        # Update UI from worker thread
        self.call_from_thread(self._log, "Success!")
        
    finally:
        # Mark complete from worker thread
        modal.call_from_thread(
            modal.mark_complete,
            success=True,
            message="✓ Complete!"
        )
```

### Widget Import Pattern
```python
from textual.widget import Widget  # Singular! Not widgets
from textual.widgets import Button, Input, ...  # Plural for UI widgets
```

### Tab Embedding Pattern
```python
# In ProjectDetailScreen.compose():
with TabPane("Image → Heightmap", id="workflow-image-tab"):
    from bathy.ui.widgets.workflow_image_widget import WorkflowImageWidget
    yield WorkflowImageWidget()  # Widget, not Screen
```

## Testing

### Manual Test Steps
1. Launch TUI: `pixi run bathy`
2. Navigate to "Open Project" and select a project
3. Click on "Image → Heightmap" tab
4. Verify workflow UI is visible (not a new screen)
5. Select an image file
6. Click "Process" button
7. **Expected**: Modal appears immediately with spinner
8. **Expected**: Logs stream live in collapsible debug section
9. **Expected**: Status updates during processing
10. **Expected**: Modal shows completion message when done
11. **Expected**: Main workflow status log shows summary after closing modal

### Automated Test
```bash
# Import test
pixi run uv run python -c "
from bathy.ui.widgets.workflow_image_widget import WorkflowImageWidget
from bathy.ui.widgets.workflow_mesh_widget import WorkflowMeshWidget
from bathy.ui.screens.processing_modal import ProcessingModal
print('✓ Imports successful')
"

# Startup test
timeout 3 pixi run bathy 2>&1 | grep -E "(ERROR|Exception)" || echo "✓ No startup errors"
```

## Benefits

1. **Modal appears immediately** - No more frozen UI waiting for processing
2. **Live log streaming** - Users can see progress in real-time
3. **Better UX** - Workflows are integrated into project view, not separate screens
4. **Cleaner navigation** - No back-and-forth between screens
5. **Thread-safe UI updates** - Proper use of `call_from_thread()`

## Next Steps

1. Test with real image processing workflow
2. Test with real mesh generation workflow
3. Verify error handling works correctly
4. Consider adding progress bars for long operations
5. Clean up deprecated screen files after testing confirms everything works

## Notes

- The `@work` decorator from Textual runs code in a worker thread
- ALL UI operations from worker threads MUST use `call_from_thread()`
- Modal uses `ModalScreen` which provides automatic dimming and layering
- Widgets can be embedded anywhere, Screens are always full-screen overlays
