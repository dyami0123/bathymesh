# Assignment 1: Python HTTP Server Basics

## Goal
Create a simple Python HTTP server that can serve static files and respond to basic API requests. This will be the foundation for your Bathymesh backend.

## Background
You'll use Flask (lightweight) or FastAPI (modern, async) to create a web server. FastAPI is recommended as it has automatic API documentation and excellent TypeScript integration via OpenAPI.

## Tasks

### 1. Install FastAPI and Dependencies
```bash
# From the bathymesh root directory
uv add fastapi uvicorn python-multipart
```

### 2. Create Basic Server
Create `server/main.py`:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Bathymesh API", version="0.1.0")

# Enable CORS so your frontend can talk to the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],  # Vite/React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Bathymesh API", "version": "0.1.0"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/info")
async def get_info():
    """Return basic info about the Bathymesh library"""
    return {
        "name": "Bathymesh",
        "description": "Convert maps and heightmaps to 3D printable meshes",
        "features": [
            "Simple surface meshes",
            "Contour-based meshes",
            "Multiple export formats (STL, PLY, OBJ)",
        ],
    }
```

### 3. Create a Run Script
Create `server/run.py`:

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "server.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
    )
```

### 4. Start the Server
```bash
python server/run.py
```

### 5. Test Your Endpoints
Open a browser or use curl:
```bash
# Test root endpoint
curl http://localhost:8000/

# Test health check
curl http://localhost:8000/api/health

# Test info endpoint
curl http://localhost:8000/api/info

# View auto-generated API docs
# Open http://localhost:8000/docs in browser
```

## Success Criteria
- ✅ FastAPI installed
- ✅ Server runs without errors
- ✅ All endpoints return JSON responses
- ✅ CORS is enabled
- ✅ API documentation accessible at /docs
- ✅ You understand the basic request/response cycle

## Challenges (Optional)
1. Add a `/api/config/defaults` endpoint that returns `MeshGenerationConfig` defaults
2. Add request logging middleware
3. Create a `/api/version` endpoint that reads from `pyproject.toml`

## Key Concepts
- **FastAPI**: Modern Python web framework with automatic API docs
- **CORS**: Cross-Origin Resource Sharing - needed for frontend to talk to backend
- **Uvicorn**: ASGI server that runs your FastAPI app
- **Auto-reload**: Server restarts when you change code (development only)

## Next Steps
Assignment 2 will create a TypeScript frontend that connects to this backend.

## Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
