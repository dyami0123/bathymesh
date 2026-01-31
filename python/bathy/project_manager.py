"""Project management for bathymesh filesystem database.

This module provides a project-centric interface for managing bathymesh workflows,
including creating projects, loading/saving configurations, and organizing files.
"""

import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

import yaml

from bathy.config import ImageProcessingConfig, MeshGenerationConfig
from bathy.config_io import ConfigIOError, load_config, save_config

logger = logging.getLogger(__name__)


class ProjectError(Exception):
    """Exception raised for project management errors."""

    pass


@dataclass
class ProjectMetadata:
    """Metadata for a bathymesh project."""

    name: str
    created: str  # ISO format timestamp
    modified: str  # ISO format timestamp
    description: str = ""
    status: str = "none"  # none, image_loaded, heightmap_generated, mesh_generated
    source_image: Optional[str] = None
    heightmap_file: Optional[str] = None
    latest_mesh: Optional[str] = None
    workflow_history: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert metadata to dictionary for YAML serialization."""
        return {
            "name": self.name,
            "created": self.created,
            "modified": self.modified,
            "description": self.description,
            "status": self.status,
            "source_image": self.source_image,
            "heightmap_file": self.heightmap_file,
            "latest_mesh": self.latest_mesh,
            "workflow_history": self.workflow_history,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectMetadata":
        """Create metadata from dictionary."""
        return cls(
            name=data["name"],
            created=data["created"],
            modified=data["modified"],
            description=data.get("description", ""),
            status=data.get("status", "none"),
            source_image=data.get("source_image"),
            heightmap_file=data.get("heightmap_file"),
            latest_mesh=data.get("latest_mesh"),
            workflow_history=data.get("workflow_history", []),
        )


@dataclass
class ProjectInfo:
    """Summary information about a project for listing."""

    name: str
    description: str
    status: str
    created: str
    modified: str
    project_dir: Path


class Project:
    """Represents a single bathymesh project with associated files and configs."""

    def __init__(self, project_dir: Path) -> None:
        """Initialize a project.

        Args:
            project_dir: Path to the project directory

        Raises:
            ProjectError: If project directory is invalid
        """
        self.project_dir = project_dir

        if not project_dir.exists():
            raise ProjectError(f"Project directory does not exist: {project_dir}")

        self.metadata_file = project_dir / "project.yaml"
        self.image_config_file = project_dir / "image_config.yaml"
        self.mesh_config_file = project_dir / "mesh_config.yaml"

        self.source_dir = project_dir / "source"
        self.heightmap_dir = project_dir / "heightmap"
        self.meshes_dir = project_dir / "meshes"

        # Load or initialize metadata
        if self.metadata_file.exists():
            self.metadata = self.load_metadata()
        else:
            # Create default metadata for existing directory
            self.metadata = ProjectMetadata(
                name=project_dir.name,
                created=datetime.now().isoformat(),
                modified=datetime.now().isoformat(),
            )
            self.save_metadata()

    def load_metadata(self) -> ProjectMetadata:
        """Load project metadata from file.

        Returns:
            ProjectMetadata object

        Raises:
            ProjectError: If loading fails
        """
        try:
            with open(self.metadata_file, "r") as f:
                data = yaml.safe_load(f)
            return ProjectMetadata.from_dict(data)
        except Exception as e:
            raise ProjectError(f"Failed to load project metadata: {e}")

    def save_metadata(self) -> None:
        """Save project metadata to file.

        Raises:
            ProjectError: If saving fails
        """
        try:
            self.metadata.modified = datetime.now().isoformat()
            with open(self.metadata_file, "w") as f:
                yaml.dump(
                    self.metadata.to_dict(),
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                )
            logger.debug(f"Saved metadata for project: {self.metadata.name}")
        except Exception as e:
            raise ProjectError(f"Failed to save project metadata: {e}")

    def load_image_config(self) -> ImageProcessingConfig:
        """Load image processing configuration.

        Returns:
            ImageProcessingConfig object

        Raises:
            ProjectError: If loading fails
        """
        try:
            if not self.image_config_file.exists():
                # Return default config
                return ImageProcessingConfig()
            return load_config(self.image_config_file, "image")
        except ConfigIOError as e:
            raise ProjectError(f"Failed to load image config: {e}")

    def save_image_config(self, config: ImageProcessingConfig) -> None:
        """Save image processing configuration.

        Args:
            config: Configuration to save

        Raises:
            ProjectError: If saving fails
        """
        try:
            save_config(config, self.image_config_file)
            self.save_metadata()  # Update modification time
        except ConfigIOError as e:
            raise ProjectError(f"Failed to save image config: {e}")

    def load_mesh_config(self) -> MeshGenerationConfig:
        """Load mesh generation configuration.

        Returns:
            MeshGenerationConfig object

        Raises:
            ProjectError: If loading fails
        """
        try:
            if not self.mesh_config_file.exists():
                # Return default config
                return MeshGenerationConfig()
            return load_config(self.mesh_config_file, "mesh")
        except ConfigIOError as e:
            raise ProjectError(f"Failed to load mesh config: {e}")

    def save_mesh_config(self, config: MeshGenerationConfig) -> None:
        """Save mesh generation configuration.

        Args:
            config: Configuration to save

        Raises:
            ProjectError: If saving fails
        """
        try:
            save_config(config, self.mesh_config_file)
            self.save_metadata()  # Update modification time
        except ConfigIOError as e:
            raise ProjectError(f"Failed to save mesh config: {e}")

    def set_source_image(self, image_path: Path) -> None:
        """Set the source image for this project.

        Copies the image to the project's source directory.

        Args:
            image_path: Path to the source image

        Raises:
            ProjectError: If operation fails
        """
        try:
            if not image_path.exists():
                raise ProjectError(f"Source image not found: {image_path}")

            self.source_dir.mkdir(parents=True, exist_ok=True)

            # Copy to project source directory
            dest_path = self.source_dir / image_path.name
            shutil.copy2(image_path, dest_path)

            # Update metadata
            self.metadata.source_image = f"source/{image_path.name}"
            self.metadata.status = "image_loaded"
            self.metadata.workflow_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "set_source_image",
                    "file": str(image_path),
                }
            )
            self.save_metadata()

            logger.info(f"Set source image: {image_path.name}")

        except Exception as e:
            raise ProjectError(f"Failed to set source image: {e}")

    def get_source_image(self) -> Optional[Path]:
        """Get the path to the project's source image.

        Returns:
            Path to source image or None if not set
        """
        if self.metadata.source_image:
            return self.project_dir / self.metadata.source_image
        return None

    def get_heightmap(self) -> Optional[Path]:
        """Get the path to the project's heightmap.

        Returns:
            Path to heightmap or None if not generated
        """
        if self.metadata.heightmap_file:
            return self.project_dir / self.metadata.heightmap_file
        return None

    def set_heightmap(self, heightmap_path: Path) -> None:
        """Set the heightmap file for this project.

        Args:
            heightmap_path: Path to the generated heightmap

        Raises:
            ProjectError: If operation fails
        """
        try:
            if not heightmap_path.exists():
                raise ProjectError(f"Heightmap file not found: {heightmap_path}")

            # Update metadata
            relative_path = heightmap_path.relative_to(self.project_dir)
            self.metadata.heightmap_file = str(relative_path)
            self.metadata.status = "heightmap_generated"
            self.metadata.workflow_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "heightmap_generated",
                    "file": str(relative_path),
                }
            )
            self.save_metadata()

            logger.info(f"Set heightmap: {relative_path}")

        except Exception as e:
            raise ProjectError(f"Failed to set heightmap: {e}")

    def get_latest_mesh(self) -> Optional[Path]:
        """Get the path to the latest generated mesh.

        Returns:
            Path to latest mesh or None if not generated
        """
        if self.metadata.latest_mesh:
            return self.project_dir / self.metadata.latest_mesh
        return None

    def set_latest_mesh(self, mesh_path: Path) -> None:
        """Set the latest mesh file for this project.

        Args:
            mesh_path: Path to the generated mesh

        Raises:
            ProjectError: If operation fails
        """
        try:
            if not mesh_path.exists():
                raise ProjectError(f"Mesh file not found: {mesh_path}")

            # Update metadata
            relative_path = mesh_path.relative_to(self.project_dir)
            self.metadata.latest_mesh = str(relative_path)
            self.metadata.status = "mesh_generated"
            self.metadata.workflow_history.append(
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "mesh_generated",
                    "file": str(relative_path),
                }
            )
            self.save_metadata()

            logger.info(f"Set latest mesh: {relative_path}")

        except Exception as e:
            raise ProjectError(f"Failed to set latest mesh: {e}")

    def list_meshes(self) -> list[Path]:
        """List all mesh files in the project.

        Returns:
            List of paths to mesh files
        """
        if not self.meshes_dir.exists():
            return []

        mesh_files = []
        for pattern in ["*.stl", "*.obj", "*.ply", "*.off", "*.3mf"]:
            mesh_files.extend(self.meshes_dir.glob(pattern))

        return sorted(mesh_files, key=lambda p: p.stat().st_mtime, reverse=True)


class ProjectManager:
    """Manages multiple bathymesh projects in a root directory."""

    def __init__(self, projects_root: Path) -> None:
        """Initialize the project manager.

        Args:
            projects_root: Root directory containing all projects
        """
        self.projects_root = projects_root
        self.projects_root.mkdir(parents=True, exist_ok=True)

    def list_projects(self) -> list[ProjectInfo]:
        """List all projects in the root directory.

        Returns:
            List of ProjectInfo objects
        """
        projects = []

        for project_dir in self.projects_root.iterdir():
            if not project_dir.is_dir():
                continue

            # Check if it's a valid project (has project.yaml)
            metadata_file = project_dir / "project.yaml"
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, "r") as f:
                    data = yaml.safe_load(f)
                    metadata = ProjectMetadata.from_dict(data)

                projects.append(
                    ProjectInfo(
                        name=metadata.name,
                        description=metadata.description,
                        status=metadata.status,
                        created=metadata.created,
                        modified=metadata.modified,
                        project_dir=project_dir,
                    )
                )
            except Exception as e:
                logger.warning(
                    f"Failed to load project metadata from {project_dir}: {e}"
                )
                continue

        # Sort by modification time (most recent first)
        projects.sort(key=lambda p: p.modified, reverse=True)
        return projects

    def create_project(self, name: str, description: str = "") -> Project:
        """Create a new project.

        Args:
            name: Name of the project (used as directory name)
            description: Optional project description

        Returns:
            New Project object

        Raises:
            ProjectError: If project already exists or creation fails
        """
        # Sanitize project name
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).lower()
        if not safe_name:
            raise ProjectError("Invalid project name")

        project_dir = self.projects_root / safe_name

        if project_dir.exists():
            raise ProjectError(f"Project already exists: {safe_name}")

        try:
            # Create project structure
            project_dir.mkdir(parents=True)
            (project_dir / "source").mkdir()
            (project_dir / "heightmap").mkdir()
            (project_dir / "meshes").mkdir()

            # Create metadata
            metadata = ProjectMetadata(
                name=name,
                created=datetime.now().isoformat(),
                modified=datetime.now().isoformat(),
                description=description,
                status="none",
            )

            # Save metadata
            metadata_file = project_dir / "project.yaml"
            with open(metadata_file, "w") as f:
                yaml.dump(
                    metadata.to_dict(), f, default_flow_style=False, sort_keys=False
                )

            # Create default configs
            project = Project(project_dir)
            project.save_image_config(ImageProcessingConfig())
            project.save_mesh_config(MeshGenerationConfig())

            logger.info(f"Created new project: {name}")
            return project

        except Exception as e:
            # Clean up on failure
            if project_dir.exists():
                shutil.rmtree(project_dir)
            raise ProjectError(f"Failed to create project: {e}")

    def load_project(self, name: str) -> Project:
        """Load an existing project by name.

        Args:
            name: Name of the project

        Returns:
            Project object

        Raises:
            ProjectError: If project doesn't exist or loading fails
        """
        # Try exact match first
        project_dir = self.projects_root / name

        if not project_dir.exists():
            # Try case-insensitive search
            for d in self.projects_root.iterdir():
                if d.is_dir() and d.name.lower() == name.lower():
                    project_dir = d
                    break
            else:
                raise ProjectError(f"Project not found: {name}")

        return Project(project_dir)

    def delete_project(self, name: str, confirm: bool = False) -> None:
        """Delete a project and all its files.

        Args:
            name: Name of the project
            confirm: Safety flag - must be True to actually delete

        Raises:
            ProjectError: If project doesn't exist or deletion fails
        """
        if not confirm:
            raise ProjectError("Must confirm deletion with confirm=True")

        project = self.load_project(name)

        try:
            shutil.rmtree(project.project_dir)
            logger.info(f"Deleted project: {name}")
        except Exception as e:
            raise ProjectError(f"Failed to delete project: {e}")
