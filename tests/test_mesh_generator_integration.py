"""Integration tests for MeshGenerator with heightmap splitting."""

import numpy as np
import open3d as o3d
import pytest

from bathy.config import (
    HeightmapSplittingConfig,
    HeighmapProcessingConfig,
    MeshGenerationConfig,
    MeshUnits,
)
from bathy.data_model import HeightmapData
from bathy.mesh_generator import MeshGenerator


def create_gradient_heightmap(width: int, height: int) -> np.ndarray:
    """Create a gradient heightmap for testing.

    Values range from 0 at top-left to (width + height - 2) at bottom-right.
    """
    y = np.arange(height).reshape(-1, 1)
    x = np.arange(width).reshape(1, -1)
    return (x + y).astype(float)


class TestMeshGeneratorWithTiling:
    """Test MeshGenerator with heightmap-based tiling."""

    def test_tiled_combined_mesh_has_correct_bounds(self) -> None:
        """Combined mesh should span the full extent of all tiles."""
        # Create a 100x100 pixel heightmap
        heightmap = create_gradient_heightmap(100, 100)

        # Config with 1:1 pixel to mm mapping, split into 2x2 grid
        config = MeshGenerationConfig(
            heightmap_processing=HeighmapProcessingConfig(
                mesh_units=MeshUnits(units_x=1.0, units_y=1.0, units_z=0.1),
                thresholds=[5.0, 10.0, 15.0],
                base_height=0.0,
                layer_thickness=0.5,
                exterior_buffer_width=2,
                exterior_buffer_value=0.0,
            ),
            heightmap_splitting=HeightmapSplittingConfig(
                enabled=True,
                splits_x=[50.0],  # Split at 50mm -> 2 columns
                splits_y=[50.0],  # Split at 50mm -> 2 rows
            ),
        )

        generator = MeshGenerator(config)
        heightmap_data = HeightmapData(data=heightmap.copy())
        heightmap_data.post_process(config)

        result = generator.execute(heightmap_data)

        assert result is not None
        assert result.combined_mesh is not None
        assert len(result.combined_mesh.vertices) > 0

        # Check that the combined mesh spans the expected range
        vertices = np.asarray(result.combined_mesh.vertices)
        min_coords = vertices.min(axis=0)
        max_coords = vertices.max(axis=0)

        # The mesh should span roughly 0-100mm in X and Y (with buffer adjustments)
        # Allow some tolerance for buffer and mesh generation variations
        assert max_coords[0] > 80, f"X max should be > 80, got {max_coords[0]}"
        assert max_coords[1] > 80, f"Y max should be > 80, got {max_coords[1]}"

    def test_individual_tiles_at_origin(self) -> None:
        """Individual tile meshes should be at local origin (0,0)."""
        heightmap = create_gradient_heightmap(100, 100)

        config = MeshGenerationConfig(
            heightmap_processing=HeighmapProcessingConfig(
                mesh_units=MeshUnits(units_x=1.0, units_y=1.0, units_z=0.1),
                thresholds=[5.0, 10.0],
                base_height=0.0,
                layer_thickness=0.5,
                exterior_buffer_width=2,
                exterior_buffer_value=0.0,
            ),
            heightmap_splitting=HeightmapSplittingConfig(
                enabled=True,
                splits_x=[50.0],
                splits_y=[50.0],
            ),
        )

        generator = MeshGenerator(config)
        heightmap_data = HeightmapData(data=heightmap.copy())
        heightmap_data.post_process(config)

        result = generator.execute(heightmap_data)

        assert result is not None
        assert len(result.split_meshes) == 4, "Should have 4 tiles (2x2 grid)"

        # Each individual tile mesh should start near origin
        for i, tile_mesh in enumerate(result.split_meshes):
            vertices = np.asarray(tile_mesh.vertices)
            min_coords = vertices.min(axis=0)
            # Tiles should start near (0, 0) - within buffer tolerance
            assert min_coords[0] < 10, (
                f"Tile {i} X min should be < 10, got {min_coords[0]}"
            )
            assert min_coords[1] < 10, (
                f"Tile {i} Y min should be < 10, got {min_coords[1]}"
            )

    def test_tile_offsets_stored_correctly(self) -> None:
        """Tile offsets should be stored for visualization."""
        heightmap = create_gradient_heightmap(100, 100)

        config = MeshGenerationConfig(
            heightmap_processing=HeighmapProcessingConfig(
                mesh_units=MeshUnits(units_x=1.0, units_y=1.0, units_z=0.1),
                thresholds=[5.0],
                base_height=0.0,
                layer_thickness=0.5,
                exterior_buffer_width=0,
                exterior_buffer_value=0.0,
            ),
            heightmap_splitting=HeightmapSplittingConfig(
                enabled=True,
                splits_x=[50.0],
                splits_y=[50.0],
            ),
        )

        generator = MeshGenerator(config)
        heightmap_data = HeightmapData(data=heightmap.copy())
        heightmap_data.post_process(config)

        generator.execute(heightmap_data)

        # Check tile offsets are stored
        assert len(generator.tile_offsets) == 4
        assert "r0c0" in generator.tile_offsets
        assert "r0c1" in generator.tile_offsets
        assert "r1c0" in generator.tile_offsets
        assert "r1c1" in generator.tile_offsets

        # Check offset values make sense
        # r0c0 should be at origin
        assert generator.tile_offsets["r0c0"] == (0.0, 0.0)
        # r0c1 should be offset in X by 50
        assert generator.tile_offsets["r0c1"][0] == pytest.approx(50.0)
        assert generator.tile_offsets["r0c1"][1] == pytest.approx(0.0)
        # r1c0 should be offset in Y by 50
        assert generator.tile_offsets["r1c0"][0] == pytest.approx(0.0)
        assert generator.tile_offsets["r1c0"][1] == pytest.approx(50.0)
        # r1c1 should be offset in both
        assert generator.tile_offsets["r1c1"][0] == pytest.approx(50.0)
        assert generator.tile_offsets["r1c1"][1] == pytest.approx(50.0)

    def test_combined_mesh_tiles_not_overlapping(self) -> None:
        """Tiles in combined mesh should not overlap - each should be offset."""
        # Use a simple heightmap where we can predict mesh positions
        heightmap = np.ones((100, 100)) * 10.0  # Flat at 10

        config = MeshGenerationConfig(
            heightmap_processing=HeighmapProcessingConfig(
                mesh_units=MeshUnits(units_x=1.0, units_y=1.0, units_z=1.0),
                thresholds=[5.0],  # Single threshold below the data
                base_height=0.0,
                layer_thickness=0.5,
                exterior_buffer_width=2,
                exterior_buffer_value=0.0,
            ),
            heightmap_splitting=HeightmapSplittingConfig(
                enabled=True,
                splits_x=[50.0],  # 2 columns
                splits_y=[],  # 1 row
            ),
        )

        generator = MeshGenerator(config)
        heightmap_data = HeightmapData(data=heightmap.copy())
        heightmap_data.post_process(config)

        result = generator.execute(heightmap_data)

        assert result is not None
        assert len(result.split_meshes) == 2, "Should have 2 tiles (2x1 grid)"

        # The combined mesh should span both tiles
        vertices = np.asarray(result.combined_mesh.vertices)
        x_min, x_max = vertices[:, 0].min(), vertices[:, 0].max()

        # Combined should span roughly 0 to 100 (with buffer adjustments)
        # If tiles were not offset, all vertices would be in 0-50 range
        assert x_max > 80, (
            f"Combined mesh X max should be > 80, got {x_max} (tiles likely not offset)"
        )

    def test_result_metadata_correct(self) -> None:
        """SplitMeshResult should have correct tile metadata."""
        # Use a flat heightmap so all tiles produce meshes
        heightmap = np.ones((40, 60)) * 10.0

        config = MeshGenerationConfig(
            heightmap_processing=HeighmapProcessingConfig(
                mesh_units=MeshUnits(units_x=1.0, units_y=1.0, units_z=0.1),
                thresholds=[0.5],  # Threshold below the data value
                base_height=0.0,
                layer_thickness=0.5,
                exterior_buffer_width=2,
                exterior_buffer_value=0.0,
            ),
            heightmap_splitting=HeightmapSplittingConfig(
                enabled=True,
                splits_x=[20.0, 40.0],  # 3 columns
                splits_y=[20.0],  # 2 rows
            ),
        )

        generator = MeshGenerator(config)
        heightmap_data = HeightmapData(data=heightmap.copy())
        heightmap_data.post_process(config)

        result = generator.execute(heightmap_data)

        assert result is not None
        assert result.tile_grid == (2, 3), f"Expected (2, 3), got {result.tile_grid}"
        assert len(result.tile_ids) == 6, (
            f"Expected 6 tiles, got {len(result.tile_ids)}"
        )
        assert result.has_splits is True

        # Verify tile IDs
        expected_ids = ["r0c0", "r0c1", "r0c2", "r1c0", "r1c1", "r1c2"]
        assert sorted(result.tile_ids) == sorted(expected_ids)


class TestMeshGeneratorWithoutTiling:
    """Test MeshGenerator without tiling (single mesh output)."""

    def test_single_mesh_no_tiling(self) -> None:
        """Without tiling, should produce a single mesh."""
        heightmap = create_gradient_heightmap(50, 50)

        config = MeshGenerationConfig(
            heightmap_processing=HeighmapProcessingConfig(
                mesh_units=MeshUnits(units_x=1.0, units_y=1.0, units_z=0.1),
                thresholds=[5.0, 10.0],
                base_height=0.0,
                layer_thickness=0.5,
                exterior_buffer_width=2,
                exterior_buffer_value=0.0,
            ),
            heightmap_splitting=HeightmapSplittingConfig(
                enabled=False,  # Tiling disabled
            ),
        )

        generator = MeshGenerator(config)
        heightmap_data = HeightmapData(data=heightmap.copy())
        heightmap_data.post_process(config)

        result = generator.execute(heightmap_data)

        assert result is not None
        assert result.combined_mesh is not None
        assert len(result.combined_mesh.vertices) > 0
        assert result.tile_grid == (1, 1)
        assert len(result.tile_ids) == 0  # No tiles when tiling disabled
