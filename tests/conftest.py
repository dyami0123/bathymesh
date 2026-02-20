"""Configuration and fixtures for pytest."""

import pytest
import numpy as np
import tempfile
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator


@dataclass
class MeshScaling:
    """Mesh scaling parameters (for test compatibility)."""

    scale_x: float = 1.0
    scale_y: float = 1.0
    scale_z: float = 1.0


def create_test_heightmap(
    width: int = 10,
    height: int = 10,
    feature_scale: float = 5.0,
    noise_level: float = 0.05,
) -> np.ndarray:
    """Create a synthetic test heightmap with features.

    Args:
        width: Width of the heightmap
        height: Height of the heightmap
        feature_scale: Scale factor for feature heights
        noise_level: Amount of random noise to add

    Returns:
        2D numpy array with synthetic heightmap data
    """
    x = np.linspace(0, 2 * np.pi, width)
    y = np.linspace(0, 2 * np.pi, height)
    X, Y = np.meshgrid(x, y)

    # Create a heightmap with hills and valleys
    heightmap = np.sin(X) * np.cos(Y) * feature_scale
    heightmap += noise_level * np.random.randn(height, width)

    return heightmap


@pytest.fixture
def test_heightmap() -> np.ndarray:
    """Create a small test heightmap for testing."""
    return create_test_heightmap(
        width=10, height=10, feature_scale=5.0, noise_level=0.05
    )


@pytest.fixture
def medium_heightmap() -> np.ndarray:
    """Create a medium-sized test heightmap for testing."""
    return create_test_heightmap(
        width=30, height=30, feature_scale=8.0, noise_level=0.1
    )


@pytest.fixture
def simple_heightmap() -> np.ndarray:
    """Create a simple heightmap with predictable values."""
    x = np.linspace(0, 1, 5)
    y = np.linspace(0, 1, 5)
    X, Y = np.meshgrid(x, y)
    return X + Y  # Simple linear gradient


@pytest.fixture
def flat_heightmap() -> np.ndarray:
    """Create a flat heightmap for edge case testing."""
    return np.ones((5, 5))


@pytest.fixture
def empty_heightmap() -> np.ndarray:
    """Create an empty heightmap for edge case testing."""
    return np.zeros((5, 5))


@pytest.fixture
def default_scaling() -> MeshScaling:
    """Default mesh scaling parameters."""
    return MeshScaling(scale_x=1.0, scale_y=1.0, scale_z=1.0)


@pytest.fixture
def custom_scaling() -> MeshScaling:
    """Custom mesh scaling parameters."""
    return MeshScaling(scale_x=0.5, scale_y=0.5, scale_z=2.0)


@pytest.fixture
def temp_output_dir() -> Iterator[Path]:
    """Create a temporary directory for test outputs."""
    temp_dir = Path(tempfile.mkdtemp())
    try:
        yield temp_dir
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def invalid_heightmap() -> np.ndarray:
    """Create an invalid heightmap with NaN values."""
    heightmap = np.ones((5, 5))
    heightmap[2, 2] = np.nan
    return heightmap


@pytest.fixture
def coordinate_arrays() -> tuple[np.ndarray, np.ndarray]:
    """Create test coordinate arrays."""
    x = np.linspace(-2, 2, 10)
    y = np.linspace(-1, 1, 10)
    return x, y
