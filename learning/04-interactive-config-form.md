# Assignment 4: Interactive Configuration Form

## Goal
Build an interactive HTML form that allows users to edit mesh generation configuration with real-time validation and preview.

## Background
This assignment introduces form handling, input validation, and state management in TypeScript. You'll create a dynamic UI that updates as users change settings.

## Tasks

### 1. Create Form Component Structure
Create `frontend/src/components/ConfigForm.ts`:
```typescript
import type { MeshGenerationConfig } from "../types/config";

export class ConfigForm {
  private container: HTMLElement;
  private config: MeshGenerationConfig;
  private onUpdate?: (config: MeshGenerationConfig) => void;

  constructor(container: HTMLElement, initialConfig: MeshGenerationConfig) {
    this.container = container;
    this.config = initialConfig;
    this.render();
  }

  setUpdateCallback(callback: (config: MeshGenerationConfig) => void) {
    this.onUpdate = callback;
  }

  private render() {
    this.container.innerHTML = `
      <div class="config-form">
        <h2>Mesh Generation Configuration</h2>
        
        <!-- Mesh Units Section -->
        <section class="config-section">
          <h3>Mesh Units</h3>
          <div class="form-group">
            <label>
              X Scale:
              <input type="number" id="units_x" value="${this.config.heightmap_processing.mesh_units.units_x}" 
                     min="0" step="0.1" />
            </label>
          </div>
          <div class="form-group">
            <label>
              Y Scale:
              <input type="number" id="units_y" value="${this.config.heightmap_processing.mesh_units.units_y}" 
                     min="0" step="0.1" />
            </label>
          </div>
          <div class="form-group">
            <label>
              Z Scale:
              <input type="number" id="units_z" value="${this.config.heightmap_processing.mesh_units.units_z}" 
                     min="0" step="0.1" />
            </label>
          </div>
        </section>

        <!-- Heightmap Processing Section -->
        <section class="config-section">
          <h3>Heightmap Processing</h3>
          <div class="form-group">
            <label>
              Buffer Width:
              <input type="number" id="exterior_buffer_width" 
                     value="${this.config.heightmap_processing.exterior_buffer_width}" 
                     min="0" step="1" />
            </label>
          </div>
          <div class="form-group">
            <label>
              Layer Thickness:
              <input type="number" id="layer_thickness" 
                     value="${this.config.heightmap_processing.layer_thickness}" 
                     min="0.001" step="0.1" />
            </label>
          </div>
        </section>

        <!-- Contour Extraction Section -->
        <section class="config-section">
          <h3>Contour Extraction</h3>
          <div class="form-group">
            <label>
              Min Polygon Area:
              <input type="number" id="min_polygon_area" 
                     value="${this.config.contour_extraction.min_polygon_area}" 
                     min="0" step="0.01" />
            </label>
          </div>
          <div class="form-group">
            <label>
              Simplify Tolerance:
              <input type="number" id="simplify_tolerance" 
                     value="${this.config.contour_extraction.simplify_tolerance}" 
                     min="0" step="0.1" />
            </label>
          </div>
          <div class="form-group">
            <label>
              Max Segments:
              <input type="number" id="max_segments" 
                     value="${this.config.contour_extraction.max_segments}" 
                     min="1" step="10" />
            </label>
          </div>
        </section>

        <!-- Triangulation Section -->
        <section class="config-section">
          <h3>Triangulation</h3>
          <div class="form-group">
            <label>
              <input type="checkbox" id="add_interior_points" 
                     ${this.config.triangulation.triangulator_add_interior_points ? "checked" : ""} />
              Add Interior Points
            </label>
          </div>
          <div class="form-group">
            <label>
              Point Density:
              <input type="number" id="interior_point_density" 
                     value="${this.config.triangulation.triangulator_interior_point_density}" 
                     min="0" step="0.1" />
            </label>
          </div>
        </section>

        <!-- Post Processing Section -->
        <section class="config-section">
          <h3>Post Processing</h3>
          <div class="form-group">
            <label>
              <input type="checkbox" id="remove_degenerate" 
                     ${this.config.post_processing.remove_degenerate_triangles ? "checked" : ""} />
              Remove Degenerate Triangles
            </label>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" id="remove_duplicates" 
                     ${this.config.post_processing.remove_duplicated_vertices ? "checked" : ""} />
              Remove Duplicate Vertices
            </label>
          </div>
          <div class="form-group">
            <label>
              Voxel Size:
              <input type="number" id="voxel_size" 
                     value="${this.config.post_processing.voxel_size}" 
                     min="0.001" step="0.01" />
            </label>
          </div>
        </section>

        <div class="form-actions">
          <button id="save-config" class="primary">Save Configuration</button>
          <button id="reset-config">Reset to Defaults</button>
        </div>
      </div>
    `;

    this.attachEventListeners();
  }

  private attachEventListeners() {
    // Attach change listeners to all inputs
    const inputs = this.container.querySelectorAll("input");
    inputs.forEach((input) => {
      input.addEventListener("change", () => this.handleInputChange());
    });
  }

  private handleInputChange() {
    // Read all form values and update config
    const getValue = (id: string): string => {
      const el = document.getElementById(id) as HTMLInputElement;
      return el?.value || "";
    };

    const getChecked = (id: string): boolean => {
      const el = document.getElementById(id) as HTMLInputElement;
      return el?.checked || false;
    };

    // Update config object
    this.config.heightmap_processing.mesh_units.units_x = parseFloat(getValue("units_x"));
    this.config.heightmap_processing.mesh_units.units_y = parseFloat(getValue("units_y"));
    this.config.heightmap_processing.mesh_units.units_z = parseFloat(getValue("units_z"));
    this.config.heightmap_processing.exterior_buffer_width = parseInt(getValue("exterior_buffer_width"));
    this.config.heightmap_processing.layer_thickness = parseFloat(getValue("layer_thickness"));
    
    this.config.contour_extraction.min_polygon_area = parseFloat(getValue("min_polygon_area"));
    this.config.contour_extraction.simplify_tolerance = parseFloat(getValue("simplify_tolerance"));
    this.config.contour_extraction.max_segments = parseInt(getValue("max_segments"));
    
    this.config.triangulation.triangulator_add_interior_points = getChecked("add_interior_points");
    this.config.triangulation.triangulator_interior_point_density = parseFloat(getValue("interior_point_density"));
    
    this.config.post_processing.remove_degenerate_triangles = getChecked("remove_degenerate");
    this.config.post_processing.remove_duplicated_vertices = getChecked("remove_duplicates");
    this.config.post_processing.voxel_size = parseFloat(getValue("voxel_size"));

    // Notify parent component
    if (this.onUpdate) {
      this.onUpdate(this.config);
    }
  }

  getConfig(): MeshGenerationConfig {
    return this.config;
  }

  updateConfig(config: MeshGenerationConfig) {
    this.config = config;
    this.render();
  }
}
```

### 2. Add Styles
Create `frontend/public/styles.css`:
```css
.config-form {
  margin: 20px 0;
}

.config-section {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
  border-left: 4px solid #4a9eff;
}

.config-section h3 {
  margin-top: 0;
  color: #4a9eff;
}

.form-group {
  margin: 15px 0;
}

.form-group label {
  display: flex;
  flex-direction: column;
  gap: 5px;
  font-weight: 500;
}

.form-group input[type="number"] {
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 8px 12px;
  color: #e0e0e0;
  font-size: 14px;
  width: 200px;
}

.form-group input[type="checkbox"] {
  width: 20px;
  height: 20px;
  margin-right: 10px;
}

.form-group input:focus {
  outline: none;
  border-color: #4a9eff;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

button.primary {
  background: #4caf50;
}

button.primary:hover {
  background: #45a049;
}

.preview-section {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
  margin: 20px 0;
}

.preview-section pre {
  background: #1a1a1a;
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
```

Link it in `frontend/public/index.html`:
```html
<link rel="stylesheet" href="styles.css">
```

### 3. Integrate Form into Main App
Update `frontend/src/main.ts`:
```typescript
import { BathymeshApiClient } from "./api/client";
import { ConfigForm } from "./components/ConfigForm";

const api = new BathymeshApiClient({ baseUrl: "http://localhost:8000" });

let configForm: ConfigForm | null = null;

// Initialize the app
async function init() {
  const formContainer = document.getElementById("config-form-container");
  const statusDiv = document.getElementById("status")!;
  
  if (!formContainer) {
    console.error("Form container not found");
    return;
  }

  try {
    // Load current config
    const config = await api.getCurrentConfig();
    
    // Create form
    configForm = new ConfigForm(formContainer, config);
    
    // Set up real-time preview
    configForm.setUpdateCallback((updatedConfig) => {
      const preview = document.getElementById("config-preview");
      if (preview) {
        preview.textContent = JSON.stringify(updatedConfig, null, 2);
      }
    });

    statusDiv.textContent = "Configuration loaded";
    statusDiv.className = "status success";
  } catch (error) {
    statusDiv.textContent = `Error loading config: ${error}`;
    statusDiv.className = "status error";
  }
}

// Save button handler
document.addEventListener("click", async (e) => {
  const target = e.target as HTMLElement;
  const statusDiv = document.getElementById("status")!;
  
  if (target.id === "save-config" && configForm) {
    try {
      const config = configForm.getConfig();
      await api.updateConfig(config);
      statusDiv.textContent = "Configuration saved!";
      statusDiv.className = "status success";
    } catch (error) {
      statusDiv.textContent = `Error saving: ${error}`;
      statusDiv.className = "status error";
    }
  }
  
  if (target.id === "reset-config" && configForm) {
    try {
      await api.resetConfig();
      const config = await api.getCurrentConfig();
      configForm.updateConfig(config);
      statusDiv.textContent = "Configuration reset to defaults";
      statusDiv.className = "status success";
    } catch (error) {
      statusDiv.textContent = `Error resetting: ${error}`;
      statusDiv.className = "status error";
    }
  }
});

// Start the app
document.addEventListener("DOMContentLoaded", init);
```

### 4. Update HTML
Update `frontend/public/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bathymesh Configuration</title>
  <link rel="stylesheet" href="styles.css">
</head>
<body>
  <h1>Bathymesh Configuration</h1>
  
  <div id="status" class="status"></div>
  
  <div class="layout">
    <div id="config-form-container"></div>
    
    <div class="preview-section">
      <h3>Live Preview</h3>
      <pre id="config-preview"></pre>
    </div>
  </div>

  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

## Success Criteria
- ✅ Form renders with all configuration fields
- ✅ Changes update the preview in real-time
- ✅ Save button persists changes to backend
- ✅ Reset button reloads defaults
- ✅ Input validation works (e.g., can't enter negative numbers)
- ✅ Form is styled and user-friendly

## Testing
1. Load the page - form should populate with current config
2. Change some values - preview should update immediately
3. Click Save - should persist to backend
4. Refresh page - values should persist
5. Click Reset - should restore defaults
6. Try entering invalid values (negative numbers, etc.)

## Challenges (Optional)
1. Add tooltips explaining what each setting does
2. Add range sliders for numeric inputs
3. Create collapsible sections for each config group
4. Add a "dirty" indicator when config differs from saved state
5. Add keyboard shortcuts (Ctrl+S to save, Ctrl+R to reset)
6. Add input validation error messages
7. Create a diff view showing changes from defaults

## Key Concepts
- **Class-based components**: Encapsulating UI logic
- **Event delegation**: Handling multiple inputs efficiently
- **Two-way data binding**: Form ↔ Config object synchronization
- **Real-time updates**: Immediate feedback on changes
- **State management**: Keeping UI in sync with data

## Next Steps
Future assignments could cover:
- File upload for heightmaps
- Mesh generation endpoints
- 3D preview with Three.js
- Batch processing
- Export functionality

## Resources
- [MDN Forms Guide](https://developer.mozilla.org/en-US/docs/Learn/Forms)
- [TypeScript Classes](https://www.typescriptlang.org/docs/handbook/2/classes.html)
- [HTML Input Types](https://developer.mozilla.org/en-US/docs/Web/HTML/Element/input)
