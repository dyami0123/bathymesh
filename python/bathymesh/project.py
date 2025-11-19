"""Project management for bathymesh."""

import logging
import shutil
from pathlib import Path
from typing import Optional

from bathymesh.config import MeshConfig

logger = logging.getLogger(__name__)


class Project:
    """
    Manages the directory structure and configuration for a bathymesh project.
    
    Standard structure:
    project_root/
    ├── data/
    │   ├── raw/
    │   ├── processed/
    │   └── meshes/
    ├── configs/
    └── debug_outs/
    """

    def __init__(self, root_dir: Path):
        self.root_dir = Path(root_dir).resolve()
        self.data_dir = self.root_dir / "data"
        self.raw_dir = self.data_dir / "raw"
        self.processed_dir = self.data_dir / "processed"
        self.meshes_dir = self.data_dir / "meshes"
        self.configs_dir = self.root_dir / "configs"
        self.debug_dir = self.root_dir / "debug_outs"

        self._ensure_structure()

    def _ensure_structure(self) -> None:
        """Create necessary directories if they don't exist."""
        for d in [
            self.raw_dir,
            self.processed_dir,
            self.meshes_dir,
            self.configs_dir,
            self.debug_dir,
        ]:
            d.mkdir(parents=True, exist_ok=True)

    def get_config_path(self, name: str) -> Path:
        """Get path for a named configuration."""
        if not name.endswith(".yaml"):
            name += ".yaml"
        return self.configs_dir / name

    def load_config(self, name: str) -> MeshConfig:
        """Load a configuration by name."""
        path = self.get_config_path(name)
        return MeshConfig.load_from_yaml(path)

    def save_config(self, config: MeshConfig, name: str) -> None:
        """Save a configuration by name."""
        path = self.get_config_path(name)
        config.save_to_yaml(path)
        logger.info(f"Saved config '{name}' to {path}")

    def get_raw_path(self, filename: str) -> Path:
        return self.raw_dir / filename

    def get_processed_path(self, filename: str) -> Path:
        return self.processed_dir / filename

    def get_mesh_path(self, filename: str) -> Path:
        return self.meshes_dir / filename
