# Assignment 2: TypeScript Frontend with Bun

## Goal
Create a minimal TypeScript frontend that fetches data from your Python backend and displays it in the browser.

## Background
You'll use Bun to build a simple TypeScript application that makes HTTP requests to your FastAPI backend. We'll start with vanilla TypeScript (no framework) to understand the fundamentals.

## Prerequisites
- Assignment 1 completed (Python backend running)
- Bun installed (`curl -fsSL https://bun.sh/install | bash`)

## Tasks

### 1. Initialize Frontend Project
```bash
# From bathymesh root directory
mkdir -p frontend
cd frontend
bun init -y
```

### 2. Setup TypeScript Configuration
Create/update `frontend/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ES2022",
    "lib": ["ES2022", "DOM"],
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "resolveJsonModule": true,
    "outDir": "./dist"
  },
  "include": ["src/**/*"]
}
```

### 3. Create Project Structure
```bash
mkdir -p src/{api,types,components}
mkdir -p public
```

### 4. Define TypeScript Types
Create `frontend/src/types/api.ts`:
```typescript
/**
 * Response from the /api/info endpoint
 */
export interface ApiInfo {
  name: string;
  description: string;
  features: string[];
}

/**
 * Response from the /api/health endpoint
 */
export interface HealthStatus {
  status: string;
}

/**
 * API client configuration
 */
export interface ApiConfig {
  baseUrl: string;
}
```

### 5. Create API Client
Create `frontend/src/api/client.ts`:
```typescript
import type { ApiInfo, HealthStatus, ApiConfig } from "../types/api";

export class BathymeshApiClient {
  private baseUrl: string;

  constructor(config: ApiConfig) {
    this.baseUrl = config.baseUrl;
  }

  async getInfo(): Promise<ApiInfo> {
    const response = await fetch(`${this.baseUrl}/api/info`);
    if (!response.ok) {
      throw new Error(`Failed to fetch info: ${response.statusText}`);
    }
    return response.json();
  }

  async getHealth(): Promise<HealthStatus> {
    const response = await fetch(`${this.baseUrl}/api/health`);
    if (!response.ok) {
      throw new Error(`Failed to fetch health: ${response.statusText}`);
    }
    return response.json();
  }
}
```

### 6. Create HTML Page
Create `frontend/public/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Bathymesh UI</title>
  <style>
    body {
      font-family: system-ui, -apple-system, sans-serif;
      max-width: 800px;
      margin: 40px auto;
      padding: 0 20px;
      background: #1a1a1a;
      color: #e0e0e0;
    }
    h1 { color: #4a9eff; }
    .status { 
      padding: 10px; 
      background: #2a2a2a;
      border-radius: 4px;
      margin: 20px 0;
    }
    .success { border-left: 4px solid #4caf50; }
    .error { border-left: 4px solid #f44336; }
    ul { line-height: 1.8; }
    button {
      background: #4a9eff;
      color: white;
      border: none;
      padding: 10px 20px;
      border-radius: 4px;
      cursor: pointer;
      margin: 5px;
    }
    button:hover { background: #357abd; }
  </style>
</head>
<body>
  <h1>Bathymesh UI</h1>
  
  <div>
    <button id="checkHealth">Check Health</button>
    <button id="loadInfo">Load Info</button>
  </div>

  <div id="status" class="status"></div>
  <div id="content"></div>

  <script type="module" src="/src/main.ts"></script>
</body>
</html>
```

### 7. Create Main Application
Create `frontend/src/main.ts`:
```typescript
import { BathymeshApiClient } from "./api/client";

// Initialize API client
const api = new BathymeshApiClient({
  baseUrl: "http://localhost:8000",
});

const statusDiv = document.getElementById("status")!;
const contentDiv = document.getElementById("content")!;

// Health check button
document.getElementById("checkHealth")?.addEventListener("click", async () => {
  try {
    statusDiv.textContent = "Checking health...";
    statusDiv.className = "status";
    
    const health = await api.getHealth();
    
    statusDiv.textContent = `Backend status: ${health.status}`;
    statusDiv.className = "status success";
  } catch (error) {
    statusDiv.textContent = `Error: ${error}`;
    statusDiv.className = "status error";
  }
});

// Load info button
document.getElementById("loadInfo")?.addEventListener("click", async () => {
  try {
    statusDiv.textContent = "Loading info...";
    statusDiv.className = "status";
    
    const info = await api.getInfo();
    
    contentDiv.innerHTML = `
      <h2>${info.name}</h2>
      <p>${info.description}</p>
      <h3>Features:</h3>
      <ul>
        ${info.features.map(f => `<li>${f}</li>`).join("")}
      </ul>
    `;
    
    statusDiv.textContent = "Info loaded successfully";
    statusDiv.className = "status success";
  } catch (error) {
    statusDiv.textContent = `Error: ${error}`;
    statusDiv.className = "status error";
  }
});

// Load info on page load
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("loadInfo")?.click();
});
```

### 8. Run the Frontend
```bash
# From frontend directory
bun --bun run public/index.html
```

Bun will start a dev server (usually on http://localhost:3000).

## Success Criteria
- ✅ Frontend runs without errors
- ✅ Health check button works
- ✅ Info loads from backend
- ✅ Error handling works (try stopping the backend)
- ✅ TypeScript types are enforced
- ✅ You understand client-server communication

## Testing
1. Start backend: `python server/run.py`
2. Start frontend: `bun --bun run public/index.html`
3. Click "Check Health" - should show "healthy"
4. Click "Load Info" - should display Bathymesh info
5. Stop the backend and try again - should show errors

## Challenges (Optional)
1. Add loading spinners while fetching data
2. Add a retry mechanism for failed requests
3. Create a `useApi` composable that handles loading/error states
4. Add request/response logging to the API client

## Key Concepts
- **Fetch API**: Modern way to make HTTP requests in browsers
- **async/await**: Handle asynchronous operations
- **TypeScript interfaces**: Type-safe API responses
- **CORS**: Why you needed it in Assignment 1
- **Separation of concerns**: API client vs UI logic

## Next Steps
Assignment 3 will add REST API endpoints for mesh generation configuration.

## Resources
- [Bun Runtime APIs](https://bun.sh/docs/api/http)
- [MDN Fetch API](https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
