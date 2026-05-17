from .job_runner import job_runner, JobStatus

from .generate_mesh import generate_mesh
from .process_image import process_image
from bathy.database_interface import DatabaseInterface
from typing import Literal
from dataclasses import dataclass
from bathy.data_model import HeightmapData
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


LARGEINT = 999_999_999_999


class HeightmapParams(BaseModel):
    is_preview: bool
    max_dimension_override: int | None = None

    def get_max_dimension(self) -> int:

        _PREVEW_MAX_DIM = 150
        max_dimension_override = self.max_dimension_override

        if self.is_preview:
            if (max_dimension_override is not None) and (
                max_dimension_override > _PREVEW_MAX_DIM
            ):
                logger.info(
                    f"Overriding max dimension to {_PREVEW_MAX_DIM} for preview heightmap"
                )
                max_dim = _PREVEW_MAX_DIM
            else:
                max_dim = max_dimension_override or LARGEINT
        else:
            max_dim = max_dimension_override or LARGEINT

        if max_dim <= 0:
            raise ValueError("max_dimension_override must be greater than 0")

        logger.info(f"Using max dimension of {max_dim} for heightmap calculation")
        logger.debug(
            f"Parameters: is_preview={self.is_preview}, max_dimension_override={self.max_dimension_override}"
        )
        return max_dim


class MeshGenerationParams(BaseModel):
    pass


def submit_job(
    project_id: str,
    job_type: Literal["calculate_heightmap", "generate_mesh"],
    params: HeightmapParams | MeshGenerationParams | None = None,
) -> JobStatus:

    if job_type == "calculate_heightmap":
        # TODO: add type check for params if we add a new job type

        def run_heightmap_job():
            project_config = DatabaseInterface.get_config(project_id=project_id)
            max_dimension = min(
                (params.get_max_dimension() if params is not None else LARGEINT),
                (project_config.image_processing.max_dimension or LARGEINT),
            )
            logger.info(
                f"Final Max dimension for heightmap calculation: {max_dimension}"
            )
            logger.info(f"Params: {params}")

            is_preview = False if params is None else params.is_preview

            image_data = DatabaseInterface.get_image_data(
                project_id=project_id, max_dimension=max_dimension
            )

            if image_data is None:
                raise ValueError(f"No image found for project '{project_id}'")

            result = process_image(
                image_path_or_data=image_data.data,
                project_config=DatabaseInterface.get_config(project_id=project_id),
            )

            DatabaseInterface.set_heightmap_data(
                project_id=project_config.project_id,
                heightmap_data=HeightmapData(
                    data=result,
                ),
                is_preview=is_preview,
            )

            return {
                "projectId": project_id,
                "message": "Heightmap job executed",
            }

        task = run_heightmap_job
    elif job_type == "generate_mesh":

        def run_mesh_job():
            project_config = DatabaseInterface.get_config(project_id=project_id)
            heightmap_data = DatabaseInterface.get_heightmap_data(
                project_id=project_id, is_preview=False
            )

            if heightmap_data is None:
                raise ValueError(f"No heightmap found for project '{project_id}'")

            meshdata, _ = generate_mesh(
                heightmap_data=heightmap_data.data,
                project_config=DatabaseInterface.get_config(project_id=project_id),
            )

            DatabaseInterface.set_mesh_data(
                project_id=project_config.project_id,
                mesh_data=meshdata,
            )

            return {
                "projectId": project_id,
                "message": "Mesh generation job executed",
            }

        task = run_mesh_job
    else:
        raise NotImplementedError

    return job_runner.submit_job(job_type=job_type, task=task)
