import logging
import os
from copy import deepcopy
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import cast
from bathy.config import ProjectConfig
from bathy.database_interface import DatabaseInterface
from bathy.data_model import HeightmapDataJson, HeightmapData, ImageData, JobStatus
from bathy.workflows.job_submission_interface import submit_job, HeightmapParams
from bathy.workflows.job_runner import job_runner
from bathy.transform_openapi_schemas import transform_schemas_for_output
import logging

logger = logging.getLogger(__name__)
version: str = "0.1.0"


def configure_application_logging() -> tuple[str, dict[str, object]]:
    """Configure app logger levels and return uvicorn logging config."""
    log_level_name = os.getenv("BATHYMESH_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_name, logging.INFO)

    # Ensure app loggers are not filtered before uvicorn applies dictConfig.
    logging.getLogger("bathy").setLevel(level)
    logging.getLogger("bathy").propagate = False

    uvicorn_log_config = _build_uvicorn_log_config(log_level_name)

    if log_level_name not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        return "info", uvicorn_log_config

    return log_level_name.lower(), uvicorn_log_config


def _build_uvicorn_log_config(log_level_name: str) -> dict[str, object]:
    """Build uvicorn logging config with level, file, and line in each record."""
    import uvicorn

    config: dict[str, object] = deepcopy(uvicorn.config.LOGGING_CONFIG)

    formatters = cast(dict[str, dict[str, object]], config["formatters"])
    formatters["default"][
        "fmt"
    ] = "%(asctime)s | %(levelprefix)s | %(filename)s:%(lineno)d | %(message)s"
    formatters["default"]["datefmt"] = "%H:%M:%S"
    formatters["access"]["fmt"] = (
        "%(asctime)s | %(levelprefix)s | %(filename)s:%(lineno)d | "
        '%(client_addr)s - "%(request_line)s" %(status_code)s'
    )
    formatters["access"]["datefmt"] = "%H:%M:%S"

    loggers = cast(dict[str, dict[str, object]], config["loggers"])
    loggers["bathy"] = {
        "handlers": ["default"],
        "level": log_level_name,
        "propagate": False,
    }
    loggers["uvicorn"]["level"] = log_level_name
    loggers["uvicorn.error"]["level"] = log_level_name
    loggers["uvicorn.access"]["level"] = log_level_name

    config["root"] = {
        "handlers": ["default"],
        "level": log_level_name,
    }

    return config


app = FastAPI(title="Bathymesh API", version=version)

# Save original openapi method before override
_original_openapi_method = app.openapi
_cached_openapi = None


def custom_openapi():
    """Generate OpenAPI schema with transformed defaults."""
    global _cached_openapi
    if _cached_openapi is not None:
        return _cached_openapi

    # Call original method to get base schema
    openapi_schema = _original_openapi_method()
    # Transform it
    _cached_openapi = transform_schemas_for_output(openapi_schema)
    return _cached_openapi


setattr(app, "openapi", custom_openapi)

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


# TODO: migrate to lifespan handler
@app.on_event("startup")
def start_job_runner() -> None:
    """Start background job worker when API boots."""
    job_runner.start()


@app.on_event("shutdown")
def stop_job_runner() -> None:
    """Stop background job worker when API shuts down."""
    job_runner.stop()


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


@app.put("/api/image/{project_id}")
async def set_project_image(project_id: str, image_data: ImageData) -> None:
    DatabaseInterface.set_image_data(project_id=project_id, image_data=image_data)


@app.get("/api/image/{project_id}")
async def get_project_image(
    project_id: str, max_dimension: int | None = None
) -> Response:
    image_data = DatabaseInterface.get_image_data(
        project_id=project_id, max_dimension=max_dimension
    )
    if image_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No image found for project '{project_id}'",
        )

    return Response(
        content=image_data.data,
        media_type=image_data.type,
    )


# Commented this out because this shouldnt be set externally.
# TBD if theres a use case for this
# @app.put("/api/heightmap/{project_id}")
# async def set_project_heightmap(
#     project_id: str, heightmap_data: HeightmapDataJson, is_preview: bool
# ) -> None:
#     DatabaseInterface.set_heightmap_data(
#         project_id=project_id,
#         heightmap_data=HeightmapData.convert(heightmap_data),
#         is_preview=is_preview,
#     )


@app.get("/api/heightmap/{project_id}")
async def get_project_heightmap(project_id: str, is_preview: bool) -> HeightmapDataJson:
    heightmap_data = DatabaseInterface.get_heightmap_data(
        project_id=project_id, is_preview=is_preview
    )
    if heightmap_data is None:
        raise HTTPException(
            status_code=404,
            detail=f"No heightmap found for project '{project_id}'",
        )

    return HeightmapDataJson.convert(heightmap_data)


@app.post("/api/heightmap/{project_id}")
async def calculate_project_heightmap(
    project_id: str, params: HeightmapParams | None
) -> JobStatus:
    logger.info(
        f"Received request to calculate heightmap for project {project_id} with params: {params}"
    )
    return submit_job(
        project_id=project_id, job_type="calculate_heightmap", params=params
    )


@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str) -> JobStatus:
    status = job_runner.get_job_status(job_id)
    if status is None:
        # TODO: panicking here seems like a bad idea. extend jobStatus to allow job not found.
        raise HTTPException(status_code=404, detail=f"Unknown job id: {job_id}")
    return status


def serve() -> None:
    """Run the API server with local development defaults."""
    import uvicorn

    uvicorn_log_level, uvicorn_log_config = configure_application_logging()

    uvicorn.run(
        "bathy.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level=uvicorn_log_level,
        log_config=uvicorn_log_config,
    )


if __name__ == "__main__":
    serve()
