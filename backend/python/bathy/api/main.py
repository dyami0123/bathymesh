from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bathy.config import ProjectConfig
from bathy.database import DatabaseInterface

version: str = "0.1.0"

app = FastAPI(title="Bathymesh API", version=version)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # Vite/React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Bathymesh API", "version": app.version}


@app.get("/api/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/config/defaults")
async def defaults() -> ProjectConfig:
    return ProjectConfig()


@app.get("/api/config/{project_id}")
async def get_project_config(project_id: str) -> ProjectConfig:
    return DatabaseInterface.get_config(project_id=project_id)


@app.put("/api/config/{project_id}")
async def set_project_config(project_id: str, project_config: ProjectConfig):
    DatabaseInterface.set_config(project_id=project_id, project_config=project_config)


@app.post("/api/config/validate")
async def validate_project_config(project_config: ProjectConfig) -> bool:
    return True


def serve() -> None:
    """Run the API server with local development defaults."""
    import uvicorn

    uvicorn.run(
        "bathy.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    serve()
