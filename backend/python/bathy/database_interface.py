from bathy.config import ProjectConfig
from typing import Any, Union, Literal
import numpy as np
from bathy.data_model import ImageData, MeshData, HeightmapData
import logging
from pathlib import Path
from PIL import Image
import open3d as o3d  # type: ignore
import yaml
import io

logger = logging.getLogger(__name__)

data_dir = Path(__file__).parent.parent.parent.parent / "data"


def _convert_to_native_types(obj: Any) -> Any:
    """Convert numpy types to native Python types for YAML serialization."""
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    elif isinstance(obj, dict):
        return {k: _convert_to_native_types(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_convert_to_native_types(v) for v in obj)
    return obj


class DatabaseInterfaceClass:

    def list_projects(self) -> list[str]:
        """List project IDs that have a config file in the data directory."""
        if not data_dir.exists():
            return []

        project_ids: list[str] = []
        for path in data_dir.iterdir():
            if not path.is_dir():
                continue

            config_path = path / f"{path.name}_config.yaml"
            if config_path.exists():
                project_ids.append(path.name)

        return sorted(project_ids)

    def get_config(self, project_id: str) -> ProjectConfig:
        logger.debug(f"Getting config for project: {project_id}")
        config_path = data_dir / project_id / f"{project_id}_config.yaml"
        if not config_path.exists():
            logger.warning(
                f"Config file not found for project {project_id}, returning default config"
            )
            config = ProjectConfig()
            self.set_config(project_id=project_id, project_config=config)
            return self.get_config(project_id=project_id)

        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f)

        return ProjectConfig(**config_data)

    def set_config(self, project_id: str, project_config: ProjectConfig) -> None:
        logger.debug(f"Setting config for project: {project_id}")
        project_dir = data_dir / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        config_path = project_dir / f"{project_id}_config.yaml"
        with open(config_path, "w") as f:
            converted_config = _convert_to_native_types(project_config.model_dump())
            yaml.safe_dump(converted_config, f)

    def set_image_data(self, project_id: str, image_data: ImageData) -> None:
        if image_data.type == "image/png":
            ext = "png"
        elif image_data.type == "image/jpeg":
            ext = "jpg"
        elif image_data.type == "image/tiff":
            ext = "tiff"
        else:
            logger.error(f"Unsupported image type: {image_data.type}")
            raise ValueError(f"Unsupported image type: {image_data.type}")

        image_path = data_dir / project_id / f"{project_id}_image.{ext}"
        image_path.parent.mkdir(parents=True, exist_ok=True)

        with open(image_path, "wb") as f:
            f.write(image_data.data)

        # remove old images with different extensions
        for old_ext in ["png", "jpg", "tiff"]:
            if old_ext != ext:
                old_image_path = data_dir / project_id / f"{project_id}_image.{old_ext}"
                if old_image_path.exists():
                    old_image_path.unlink()

    def get_image_data(
        self,
        project_id: str,
        max_dimension: float | None = None,
    ) -> Union[ImageData, None]:

        images = list((data_dir / project_id).glob(f"{project_id}_image.*"))
        if not images:
            logger.warning(f"No image found for project {project_id}")
            return None

        if len(images) > 1:
            logger.warning(
                f"Multiple images found for project {project_id}, using the first one"
            )

        image_path = images[0]

        image_type: Literal["image/png", "image/jpeg", "image/tiff"]
        if image_path.suffix == ".png":
            image_type = "image/png"
        elif image_path.suffix in [".jpg", ".jpeg"]:
            image_type = "image/jpeg"
        elif image_path.suffix == ".tiff":
            image_type = "image/tiff"
        else:
            logger.error(f"Unsupported image type for file: {image_path}")
            raise ValueError(f"Unsupported image type for file: {image_path}")

        if max_dimension is None:
            with open(image_path, "rb") as f:
                image_data = f.read()
        else:
            img = Image.open(image_path)
            current_max = max(img.size)

            if current_max > max_dimension:
                ratio = max_dimension / current_max
                new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                logger.info(
                    f"Resizing image to fit max dimension of {max_dimension} pixels"
                )
                with io.BytesIO() as bytes_stream:

                    img.resize(new_size, Image.Resampling.LANCZOS).save(
                        bytes_stream, format=image_type.split("/")[1]
                    )
                    bytes_stream.seek(0)
                    image_data = bytes_stream.read()
                logger.info(f"Resized to: {new_size[0]}x{new_size[1]} pixels")
            else:
                with open(image_path, "rb") as f:
                    image_data = f.read()

        return ImageData(data=image_data, type=image_type)

    def get_image_path(self, project_id: str) -> Union[Path, None]:
        """Get the file path to the stored image for a project."""
        images = list((data_dir / project_id).glob(f"{project_id}_image.*"))
        if not images:
            logger.warning(f"No image found for project {project_id}")
            return None

        if len(images) > 1:
            logger.warning(
                f"Multiple images found for project {project_id}, using the first one"
            )

        return images[0]

    def set_heightmap_data(
        self,
        project_id: str,
        heightmap_data: HeightmapData,
        is_preview: bool = False,
    ) -> None:

        heightmap_data_path = self.get_path(
            project_id, f"{project_id}_heightmap.npy", is_preview=is_preview
        )
        heightmap_params_path = self.get_path(
            project_id, f"{project_id}_heightmap_params.yaml", is_preview=is_preview
        )
        heightmap_data_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"Setting heightmap data for project: {project_id} at {heightmap_data_path}"
        )

        with open(heightmap_data_path, "wb") as f:
            np.save(f, heightmap_data.data)

        params_dict = {"post_processed": heightmap_data._post_processed}
        params_dict = _convert_to_native_types(params_dict)
        with open(heightmap_params_path, "w") as f:
            yaml.safe_dump(params_dict, f)

    def get_heightmap_data(
        self,
        project_id: str,
        is_preview: bool = False,
    ) -> Union[None, HeightmapData]:
        heightmap_data_path = self.get_path(
            project_id, f"{project_id}_heightmap.npy", is_preview=is_preview
        )
        heightmap_params_path = self.get_path(
            project_id, f"{project_id}_heightmap_params.yaml", is_preview=is_preview
        )

        if not heightmap_data_path.exists():

            logger.warning(f"No heightmap data found for project {project_id}")
            logger.info(f"No heightmap data found for project {project_id}")
            logger.debug(f"No heightmap data found for project {project_id}")
            return None

        with open(heightmap_data_path, "rb") as f:
            heightmap_array = np.load(f)

        if heightmap_params_path.exists():
            with open(heightmap_params_path, "r") as f:
                params_dict = yaml.safe_load(f)
            post_processed = params_dict.get("post_processed", False)
        else:
            post_processed = False

        return HeightmapData(data=heightmap_array, _post_processed=post_processed)

    def set_mesh_data(self, project_id: str, mesh_data: MeshData) -> None:

        mesh_data_path = self.get_path(
            project_id, f"{project_id}_meshdata.stl", is_preview=False
        )

        o3d.io.write_triangle_mesh(mesh_data_path, mesh_data.data)

    def get_mesh_data(self, project_id: str) -> MeshData:

        mesh_data_path = self.get_path(
            project_id, f"{project_id}_meshdata.stl", is_preview=False
        )

        triange_data = o3d.io.read_triangle_mesh(mesh_data_path)
        original_width: int | None = None
        original_height: int | None = None

        # STL does not store custom metadata, so recover dimensions from
        # the full-resolution heightmap used for mesh generation.
        heightmap_data = self.get_heightmap_data(
            project_id=project_id,
            is_preview=False,
        )
        if heightmap_data is not None:
            original_height, original_width = heightmap_data.data.shape

        return MeshData(
            data=triange_data,
            original_width=original_width,
            original_height=original_height,
        )

    def get_path(self, project_id: str, filename: str, is_preview: bool) -> Path:
        return data_dir / project_id / ("preview" if is_preview else "final") / filename


DatabaseInterface = DatabaseInterfaceClass()


if __name__ == "__main__":
    path = "/home/dyami/Documents/git/bathymesh/backend/data/raw/ethan.png"

    with open(path, "rb") as f:
        file_bytes = f.read()

    DatabaseInterface.set_image_data(
        "default_project",
        image_data=ImageData(data=file_bytes, type="image/png"),
    )
