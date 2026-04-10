# Assignment 3: Configuration API Endpoints

## Goal
Create REST API endpoints for managing mesh generation configuration, including fetching defaults and validating user settings.

## Background
You'll extend your FastAPI backend to expose configuration endpoints, and update your TypeScript frontend to work with these endpoints. This introduces CRUD operations and form handling.

## Tasks

### Part A: Backend Configuration API

### 1. Create Configuration Models
Create `server/models.py`:
```python
from pydantic import BaseModel, Field


class MeshUnits(BaseModel):
    units_x: float = Field(default=1.0, ge=0)
    units_y: float = Field(default=1.0, ge=0)
    units_z: float = Field(default=1.0, ge=0)


class HeightmapProcessingConfig(BaseModel):
    exterior_buffer_width: int = Field(default=0, ge=0)
    exterior_buffer_value: float = 0.0
    data_offset: float = 0.0
    mesh_units: MeshUnits = Field(default_factory=MeshUnits)
    thresholds: list[float] = Field(default_factory=lambda: [x for x in range(0, 51, 5)])
    base_height: float = 0.0
    layer_thickness: float = Field(default=0.5, gt=0)


class ContourExtractionConfig(BaseModel):
    min_polygon_area: float = Field(default=0.01, ge=0)
    simplify_tolerance: float = Field(default=0.5, ge=0)
    max_segments: int = Field(default=100, ge=1)
    min_area_fraction: float = Field(default=0.01, ge=0, le=1)


class TriangulationConfig(BaseModel):
    triangulator_add_interior_points: bool = True
    triangulator_interior_point_density: float = Field(default=1.0, ge=0)


class PostProcessingConfig(BaseModel):
    remove_degenerate_triangles: bool = True
    remove_duplicated_vertices: bool = True
    merge_close_vertices: bool = False
    target_triangle_count: int | None = Field(default=None, ge=1)
    voxel_size: float = Field(default=0.01, gt=0)


class MeshCombinationConfig(BaseModel):
    merge_threshold: float = Field(default=1e-6, ge=0)


class MeshGenerationConfig(BaseModel):
    """Complete mesh generation configuration"""
    stateless: bool = False
    heightmap_processing: HeightmapProcessingConfig = Field(
        default_factory=HeightmapProcessingConfig
    )
    contour_extraction: ContourExtractionConfig = Field(
        default_factory=ContourExtractionConfig
    )
    triangulation: TriangulationConfig = Field(
        default_factory=TriangulationConfig
    )
    post_processing: PostProcessingConfig = Field(
        default_factory=PostProcessingConfig
    )
    mesh_combination: MeshCombinationConfig = Field(
        default_factory=MeshCombinationConfig
    )
```

### 2. Add Configuration Endpoints
Update `server/main.py`:
```python
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from server.models import MeshGenerationConfig

app = FastAPI(title="Bathymesh API", version="0.1.0")

# ... (keep existing CORS setup) ...

# In-memory storage (replace with database later)
current_config: MeshGenerationConfig = MeshGenerationConfig()


@app.get("/api/config/defaults", response_model=MeshGenerationConfig)
async def get_default_config():
    """Get default mesh generation configuration"""
    return MeshGenerationConfig()


@app.get("/api/config", response_model=MeshGenerationConfig)
async def get_current_config():
    """Get current mesh generation configuration"""
    return current_config


@app.put("/api/config", response_model=MeshGenerationConfig)
async def update_config(config: MeshGenerationConfig):
    """Update mesh generation configuration"""
    global current_config
    current_config = config
    return current_config


@app.post("/api/config/validate", response_model=dict)
async def validate_config(config: MeshGenerationConfig):
    """Validate a configuration without saving it"""
    # Pydantic validation happens automatically
    return {
        "valid": True,
        "message": "Configuration is valid",
    }


@app.post("/api/config/reset")
async def reset_config():
    """Reset configuration to defaults"""
    global current_config
    current_config = MeshGenerationConfig()
    return {"message": "Configuration reset to defaults"}
```

### Part B: TypeScript Frontend Integration

### 3. Create TypeScript Types
Create `frontend/src/types/config.ts`:
```typescript
/**
 * Mirror the Python Pydantic models
 */

export interface MeshUnits {
  units_x: number;
  units_y: number;
  units_z: number;
}

export interface HeightmapProcessingConfig {
  exterior_buffer_width: number;
  exterior_buffer_value: number;
  data_offset: number;
  mesh_units: MeshUnits;
  thresholds: number[];
  base_height: number;
  layer_thickness: number;
}

export interface ContourExtractionConfig {
  min_polygon_area: number;
  simplify_tolerance: number;
  max_segments: number;
  min_area_fraction: number;
}

export interface TriangulationConfig {
  triangulator_add_interior_points: boolean;
  triangulator_interior_point_density: number;
}

export interface PostProcessingConfig {
  remove_degenerate_triangles: boolean;
  remove_duplicated_vertices: boolean;
  merge_close_vertices: boolean;
  target_triangle_count?: number;
  voxel_size: number;
}

export interface MeshCombinationConfig {
  merge_threshold: number;
}

export interface MeshGenerationConfig {
  stateless: boolean;
  heightmap_processing: HeightmapProcessingConfig;
  contour_extraction: ContourExtractionConfig;
  triangulation: TriangulationConfig;
  post_processing: PostProcessingConfig;
  mesh_combination: MeshCombinationConfig;
}
```

### 4. Extend API Client
Update `frontend/src/api/client.ts`:
```typescript
import type { MeshGenerationConfig } from "../types/config";

export class BathymeshApiClient {
  // ... existing code ...

  async getDefaultConfig(): Promise<MeshGenerationConfig> {
    const response = await fetch(`${this.baseUrl}/api/config/defaults`);
    if (!response.ok) throw new Error(`Failed to fetch defaults: ${response.statusText}`);
    return response.json();
  }

  async getCurrentConfig(): Promise<MeshGenerationConfig> {
    const response = await fetch(`${this.baseUrl}/api/config`);
    if (!response.ok) throw new Error(`Failed to fetch config: ${response.statusText}`);
    return response.json();
  }

  async updateConfig(config: MeshGenerationConfig): Promise<MeshGenerationConfig> {
    const response = await fetch(`${this.baseUrl}/api/config`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error(`Failed to update config: ${response.statusText}`);
    return response.json();
  }

  async validateConfig(config: MeshGenerationConfig): Promise<{ valid: boolean; message: string }> {
    const response = await fetch(`${this.baseUrl}/api/config/validate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    if (!response.ok) throw new Error(`Validation failed: ${response.statusText}`);
    return response.json();
  }

  async resetConfig(): Promise<{ message: string }> {
    const response = await fetch(`${this.baseUrl}/api/config/reset`, {
      method: "POST",
    });
    if (!response.ok) throw new Error(`Failed to reset config: ${response.statusText}`);
    return response.json();
  }
}
```

### 5. Create Simple Config Viewer
Update `frontend/public/index.html` to add:
```html
<div>
  <button id="loadConfig">Load Config</button>
  <button id="resetConfig">Reset to Defaults</button>
</div>
<pre id="configDisplay" style="background: #2a2a2a; padding: 20px; border-radius: 4px; overflow-x: auto;"></pre>
```

Update `frontend/src/main.ts`:
```typescript
// ... existing code ...

document.getElementById("loadConfig")?.addEventListener("click", async () => {
  try {
    const config = await api.getCurrentConfig();
    const display = document.getElementById("configDisplay");
    if (display) {
      display.textContent = JSON.stringify(config, null, 2);
    }
    statusDiv.textContent = "Config loaded";
    statusDiv.className = "status success";
  } catch (error) {
    statusDiv.textContent = `Error: ${error}`;
    statusDiv.className = "status error";
  }
});

document.getElementById("resetConfig")?.addEventListener("click", async () => {
  try {
    await api.resetConfig();
    const config = await api.getCurrentConfig();
    const display = document.getElementById("configDisplay");
    if (display) {
      display.textContent = JSON.stringify(config, null, 2);
    }
    statusDiv.textContent = "Config reset to defaults";
    statusDiv.className = "status success";
  } catch (error) {
    statusDiv.textContent = `Error: ${error}`;
    statusDiv.className = "status error";
  }
});
```

## Success Criteria
- ✅ All config endpoints work in FastAPI
- ✅ Pydantic validation catches invalid data
- ✅ TypeScript types match Python models
- ✅ Frontend can fetch and display config
- ✅ Reset button works
- ✅ API docs show all endpoints at /docs

## Testing
1. Visit http://localhost:8000/docs
2. Test each endpoint with the interactive docs
3. Try sending invalid data (negative numbers where not allowed)
4. Test from the frontend UI

## Challenges (Optional)
1. Add a PATCH endpoint to update only part of the config
2. Add config validation error messages that show which field failed
3. Create a config history/undo system
4. Add config presets (e.g., "high quality", "fast preview")

## Key Concepts
- **Pydantic**: Data validation and serialization in Python
- **REST conventions**: GET (read), PUT (update), POST (create/action)
- **Type safety**: Matching types between backend and frontend
- **JSON serialization**: Converting objects to/from JSON

## Next Steps
Assignment 4 will create an interactive form to edit configuration values.

## Resources
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [FastAPI Request Body](https://fastapi.tiangolo.com/tutorial/body/)
- [REST API Design Best Practices](https://stackoverflow.blog/2020/03/02/best-practices-for-rest-api-design/)
