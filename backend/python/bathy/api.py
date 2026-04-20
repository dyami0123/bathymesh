import logging
import os
from copy import deepcopy
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from typing import cast
from bathy.config import ProjectConfig
from bathy.database_interface import DatabaseInterface
from bathy.data_model import HeightmapDataJson, HeightmapData, ImageData, JobStatus
from bathy.workflows.job_submission_interface import submit_job, HeightmapParams
from bathy.workflows.job_runner import job_runner
from bathy.apply_openapi_overrides import apply_openapi_overrides
from bathy.api_logs import configure_application_logging
from bathy.image_processing.image_processor import ImageProcessor
from collections import OrderedDict
import logging

logger = logging.getLogger(__name__)
version: str = "0.1.0"


app = FastAPI(title="Bathymesh API", version=version)

apply_openapi_overrides(app)

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


@app.get("/api/projects")
async def list_projects() -> list[str]:
    return DatabaseInterface.list_projects()


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
async def set_project_image(
    project_id: str, file: UploadFile, update_config_colormap: bool = True
) -> None:
    # Read the uploaded file and validate type
    file_content = await file.read()

    # Map MIME types to the expected format
    valid_types = {"image/png", "image/jpeg", "image/tiff"}
    if file.content_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type. Allowed types: {', '.join(valid_types)}",
        )

    # Create ImageData object with the file content
    image_data = ImageData(data=file_content, type=file.content_type)  # type: ignore

    DatabaseInterface.set_image_data(project_id=project_id, image_data=image_data)

    if update_config_colormap:
        config = DatabaseInterface.get_config(project_id=project_id)

        sample_image_data = DatabaseInterface.get_image_data(
            project_id=project_id, max_dimension=50
        )
        if sample_image_data is None:
            raise HTTPException(
                status_code=404,
                detail=f"No image found for project after explicit write: '{project_id}'",
            )

        image_processor = ImageProcessor(config=config.image_processing)
        image_array = image_processor.load_image(sample_image_data.data)
        sorted_colors = image_processor.extract_dominant_colors(image_array, n_colors=5)

        new_colormap = OrderedDict(
            {
                color: {"fuzziness": 15, "value": i * 5 + 5}
                for i, (color, _) in enumerate(sorted_colors)
            }
        )

        config.image_processing.color_map = new_colormap
        DatabaseInterface.set_config(project_id=project_id, project_config=config)


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
