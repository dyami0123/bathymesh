"""Tests for heightmap splitting functionality."""

import numpy as np
import pytest

from bathy.config import HeightmapSplittingConfig, MeshGenerationConfig, MeshUnits
from bathy.heightmap_splitter import HeightmapSplitter, HeightmapTile


class TestHeightmapTile:
    """Tests for the HeightmapTile dataclass."""

    def test_tile_id_format(self):
        """Test that tile_id is formatted correctly."""
        tile = HeightmapTile(
            data=np.zeros((10, 10)),
            row_index=0,
            col_index=1,
            row_offset=0,
            col_offset=10,
            mesh_offset_x=50.0,
            mesh_offset_y=0.0,
        )
        assert tile.tile_id == "r0c1"

    def test_tile_id_multi_digit(self):
        """Test tile_id with multi-digit indices."""
        tile = HeightmapTile(
            data=np.zeros((10, 10)),
            row_index=12,
            col_index=5,
            row_offset=0,
            col_offset=0,
            mesh_offset_x=0.0,
            mesh_offset_y=0.0,
        )
        assert tile.tile_id == "r12c5"

    def test_shape_property(self):
        """Test that shape property returns data shape."""
        data = np.zeros((15, 20))
        tile = HeightmapTile(
            data=data,
            row_index=0,
            col_index=0,
            row_offset=0,
            col_offset=0,
            mesh_offset_x=0.0,
            mesh_offset_y=0.0,
        )
        assert tile.shape == (15, 20)

    def test_mesh_offsets_stored(self):
        """Test that mesh offsets are stored correctly."""
        tile = HeightmapTile(
            data=np.zeros((10, 10)),
            row_index=1,
            col_index=2,
            row_offset=100,
            col_offset=200,
            mesh_offset_x=150.5,
            mesh_offset_y=75.25,
        )
        assert tile.mesh_offset_x == 150.5
        assert tile.mesh_offset_y == 75.25


class TestHeightmapSplitter:
    """Tests for the HeightmapSplitter class."""

    @pytest.fixture
    def simple_heightmap(self) -> np.ndarray:
        """Create a simple 100x100 heightmap for testing."""
        x = np.linspace(0, 10, 100)
        y = np.linspace(0, 10, 100)
        X, Y = np.meshgrid(x, y)
        return X + Y

    @pytest.fixture
    def large_heightmap(self) -> np.ndarray:
        """Create a 1000x800 heightmap for testing."""
        return np.zeros((800, 1000))  # 800 rows, 1000 cols

    @pytest.fixture
    def default_units(self) -> MeshUnits:
        """Default mesh units (1:1 scaling)."""
        return MeshUnits(units_x=1.0, units_y=1.0, units_z=1.0)

    @pytest.fixture
    def half_scale_units(self) -> MeshUnits:
        """Mesh units with 0.5 scale (2 pixels per unit)."""
        return MeshUnits(units_x=0.5, units_y=0.5, units_z=1.0)

    @pytest.fixture
    def disabled_splitter(self, default_units: MeshUnits) -> HeightmapSplitter:
        """Create a splitter with splitting disabled."""
        config = HeightmapSplittingConfig(enabled=False)
        return HeightmapSplitter(config, default_units)

    @pytest.fixture
    def single_x_split_splitter(self, default_units: MeshUnits) -> HeightmapSplitter:
        """Create a splitter with one X split at position 50."""
        config = HeightmapSplittingConfig(enabled=True, splits_x=[50.0])
        return HeightmapSplitter(config, default_units)

    @pytest.fixture
    def grid_2x2_splitter(self, default_units: MeshUnits) -> HeightmapSplitter:
        """Create a splitter that splits into 2x2 grid (splits at 50,50)."""
        config = HeightmapSplittingConfig(
            enabled=True, splits_x=[50.0], splits_y=[50.0]
        )
        return HeightmapSplitter(config, default_units)

    def test_from_config(self):
        """Test HeightmapSplitter creation from MeshGenerationConfig."""
        config = MeshGenerationConfig()
        splitter = HeightmapSplitter.from_config(config)
        assert isinstance(splitter, HeightmapSplitter)
        assert splitter.config.enabled is False

    def test_disabled_returns_single_tile(
        self, simple_heightmap: np.ndarray, disabled_splitter: HeightmapSplitter
    ):
        """Test that disabled splitter returns original heightmap in single tile."""
        tiles = disabled_splitter.split_heightmap(simple_heightmap)
        assert len(tiles) == 1
        assert tiles[0].tile_id == "r0c0"
        assert np.array_equal(tiles[0].data, simple_heightmap)
        assert tiles[0].mesh_offset_x == 0.0
        assert tiles[0].mesh_offset_y == 0.0

    def test_single_x_split_creates_two_columns(
        self, simple_heightmap: np.ndarray, single_x_split_splitter: HeightmapSplitter
    ):
        """Test that one X split creates 2 columns."""
        tiles = single_x_split_splitter.split_heightmap(simple_heightmap)
        assert len(tiles) == 2
        tile_ids = [t.tile_id for t in tiles]
        assert "r0c0" in tile_ids
        assert "r0c1" in tile_ids

    def test_2x2_split_creates_four_tiles(
        self, simple_heightmap: np.ndarray, grid_2x2_splitter: HeightmapSplitter
    ):
        """Test that 2x2 grid creates exactly 4 tiles."""
        tiles = grid_2x2_splitter.split_heightmap(simple_heightmap)
        assert len(tiles) == 4

    def test_2x2_tile_ids(
        self, simple_heightmap: np.ndarray, grid_2x2_splitter: HeightmapSplitter
    ):
        """Test that 2x2 grid produces correct tile IDs."""
        tiles = grid_2x2_splitter.split_heightmap(simple_heightmap)
        tile_ids = [t.tile_id for t in tiles]
        assert "r0c0" in tile_ids
        assert "r0c1" in tile_ids
        assert "r1c0" in tile_ids
        assert "r1c1" in tile_ids

    def test_tiles_have_correct_shape(
        self, simple_heightmap: np.ndarray, grid_2x2_splitter: HeightmapSplitter
    ):
        """Test that tiles have correct shapes based on split positions."""
        tiles = grid_2x2_splitter.split_heightmap(simple_heightmap)

        # Split at 50 in 100-pixel dimension = 50+50 pixels
        for tile in tiles:
            height, width = tile.shape
            assert height == 50
            assert width == 50

    def test_tiles_cover_full_heightmap(
        self, simple_heightmap: np.ndarray, grid_2x2_splitter: HeightmapSplitter
    ):
        """Test that tiles together cover the full heightmap without gaps."""
        tiles = grid_2x2_splitter.split_heightmap(simple_heightmap)

        # Top-left tile should contain top-left corner
        r0c0 = next(t for t in tiles if t.tile_id == "r0c0")
        assert np.isclose(simple_heightmap[0, 0], r0c0.data[0, 0])

        # Top-right tile should contain top-right corner
        r0c1 = next(t for t in tiles if t.tile_id == "r0c1")
        assert np.isclose(simple_heightmap[0, -1], r0c1.data[0, -1])

        # Bottom-left tile should contain bottom-left corner
        r1c0 = next(t for t in tiles if t.tile_id == "r1c0")
        assert np.isclose(simple_heightmap[-1, 0], r1c0.data[-1, 0])

        # Bottom-right tile should contain bottom-right corner
        r1c1 = next(t for t in tiles if t.tile_id == "r1c1")
        assert np.isclose(simple_heightmap[-1, -1], r1c1.data[-1, -1])

    def test_mesh_offsets_calculated(
        self, simple_heightmap: np.ndarray, grid_2x2_splitter: HeightmapSplitter
    ):
        """Test that mesh offsets are calculated correctly."""
        tiles = grid_2x2_splitter.split_heightmap(simple_heightmap)

        # r0c0 should have offset (0, 0)
        r0c0 = next(t for t in tiles if t.tile_id == "r0c0")
        assert r0c0.mesh_offset_x == 0.0
        assert r0c0.mesh_offset_y == 0.0

        # r0c1 should have offset (50, 0) - after first X split
        r0c1 = next(t for t in tiles if t.tile_id == "r0c1")
        assert r0c1.mesh_offset_x == 50.0
        assert r0c1.mesh_offset_y == 0.0

        # r1c0 should have offset (0, 50) - after first Y split
        r1c0 = next(t for t in tiles if t.tile_id == "r1c0")
        assert r1c0.mesh_offset_x == 0.0
        assert r1c0.mesh_offset_y == 50.0

        # r1c1 should have offset (50, 50)
        r1c1 = next(t for t in tiles if t.tile_id == "r1c1")
        assert r1c1.mesh_offset_x == 50.0
        assert r1c1.mesh_offset_y == 50.0

    def test_half_scale_units_conversion(
        self, large_heightmap: np.ndarray, half_scale_units: MeshUnits
    ):
        """Test that mesh units correctly convert split positions to pixels."""
        # 1000 cols * 0.5 units/pixel = 500 mesh units wide
        # Split at 200 mesh units = 400 pixels
        config = HeightmapSplittingConfig(enabled=True, splits_x=[200.0])
        splitter = HeightmapSplitter(config, half_scale_units)

        tiles = splitter.split_heightmap(large_heightmap)

        assert len(tiles) == 2
        r0c0 = next(t for t in tiles if t.tile_id == "r0c0")
        r0c1 = next(t for t in tiles if t.tile_id == "r0c1")

        # First tile: columns 0-399 (400 pixels)
        assert r0c0.data.shape[1] == 400
        assert r0c0.col_offset == 0
        assert r0c0.mesh_offset_x == 0.0

        # Second tile: columns 400-999 (600 pixels)
        assert r0c1.data.shape[1] == 600
        assert r0c1.col_offset == 400
        assert r0c1.mesh_offset_x == 200.0

    def test_negative_units_use_absolute_value(self, large_heightmap: np.ndarray):
        """Test that negative mesh units work correctly (absolute value used)."""
        # Negative units for axis flipping
        negative_units = MeshUnits(units_x=-0.5, units_y=0.5, units_z=1.0)
        config = HeightmapSplittingConfig(enabled=True, splits_x=[200.0])
        splitter = HeightmapSplitter(config, negative_units)

        tiles = splitter.split_heightmap(large_heightmap)

        assert len(tiles) == 2
        r0c0 = next(t for t in tiles if t.tile_id == "r0c0")
        # Should still split at pixel 400 (200 / abs(-0.5))
        assert r0c0.data.shape[1] == 400

    def test_get_tile_count_disabled(self, disabled_splitter: HeightmapSplitter):
        """Test tile count when disabled."""
        assert disabled_splitter.get_tile_count() == 1

    def test_get_tile_count_2x2(self, grid_2x2_splitter: HeightmapSplitter):
        """Test tile count for 2x2 grid."""
        assert grid_2x2_splitter.get_tile_count() == 4

    def test_get_tile_count_3x2(self, default_units: MeshUnits):
        """Test tile count for 3 columns x 2 rows."""
        config = HeightmapSplittingConfig(
            enabled=True, splits_x=[33.0, 66.0], splits_y=[50.0]
        )
        splitter = HeightmapSplitter(config, default_units)
        assert splitter.get_tile_count() == 6

    def test_get_grid_dimensions_disabled(self, disabled_splitter: HeightmapSplitter):
        """Test grid dimensions when disabled."""
        assert disabled_splitter.get_grid_dimensions() == (1, 1)

    def test_get_grid_dimensions_2x2(self, grid_2x2_splitter: HeightmapSplitter):
        """Test grid dimensions for 2x2 grid."""
        assert grid_2x2_splitter.get_grid_dimensions() == (2, 2)

    def test_get_grid_dimensions_3x2(self, default_units: MeshUnits):
        """Test grid dimensions for 3 columns x 2 rows."""
        config = HeightmapSplittingConfig(
            enabled=True, splits_x=[33.0, 66.0], splits_y=[50.0]
        )
        splitter = HeightmapSplitter(config, default_units)
        # 2 X splits = 3 columns, 1 Y split = 2 rows
        assert splitter.get_grid_dimensions() == (2, 3)

    def test_iter_tiles(
        self, simple_heightmap: np.ndarray, grid_2x2_splitter: HeightmapSplitter
    ):
        """Test tile iteration."""
        tile_ids = []
        for tile in grid_2x2_splitter.iter_tiles(simple_heightmap):
            tile_ids.append(tile.tile_id)

        assert len(tile_ids) == 4
        assert "r0c0" in tile_ids


class TestHeightmapSplitterEdgeCases:
    """Edge case tests for HeightmapSplitter."""

    @pytest.fixture
    def default_units(self) -> MeshUnits:
        """Default mesh units (1:1 scaling)."""
        return MeshUnits(units_x=1.0, units_y=1.0, units_z=1.0)

    def test_single_row_tiles(self, default_units: MeshUnits):
        """Test splitting into 1 row of tiles (X splits only)."""
        config = HeightmapSplittingConfig(enabled=True, splits_x=[50.0, 100.0])
        splitter = HeightmapSplitter(config, default_units)

        heightmap = np.zeros((50, 150))
        tiles = splitter.split_heightmap(heightmap)

        assert len(tiles) == 3
        assert splitter.get_grid_dimensions() == (1, 3)

    def test_single_column_tiles(self, default_units: MeshUnits):
        """Test splitting into 1 column of tiles (Y splits only)."""
        config = HeightmapSplittingConfig(enabled=True, splits_y=[50.0, 100.0])
        splitter = HeightmapSplitter(config, default_units)

        heightmap = np.zeros((150, 50))
        tiles = splitter.split_heightmap(heightmap)

        assert len(tiles) == 3
        assert splitter.get_grid_dimensions() == (3, 1)

    def test_split_outside_range_skipped(self, default_units: MeshUnits):
        """Test that splits outside the heightmap range are skipped."""
        config = HeightmapSplittingConfig(
            enabled=True,
            splits_x=[50.0, 500.0],  # 500 is outside 100-pixel width
        )
        splitter = HeightmapSplitter(config, default_units)

        heightmap = np.zeros((100, 100))
        tiles = splitter.split_heightmap(heightmap)

        # Only the 50.0 split should be applied (500.0 is out of range)
        assert len(tiles) == 2

    def test_split_at_zero_skipped(self, default_units: MeshUnits):
        """Test that splits at position 0 are skipped (implicit boundary)."""
        config = HeightmapSplittingConfig(enabled=True, splits_x=[0.0, 50.0])
        splitter = HeightmapSplitter(config, default_units)

        heightmap = np.zeros((100, 100))
        tiles = splitter.split_heightmap(heightmap)

        # 0.0 split is ignored (implicit boundary)
        assert len(tiles) == 2

    def test_duplicate_splits_deduplicated(self, default_units: MeshUnits):
        """Test that duplicate split positions are handled."""
        config = HeightmapSplittingConfig(enabled=True, splits_x=[50.0, 50.0, 50.0])
        splitter = HeightmapSplitter(config, default_units)

        heightmap = np.zeros((100, 100))
        tiles = splitter.split_heightmap(heightmap)

        # Duplicates should be removed
        assert len(tiles) == 2

    def test_unsorted_splits_sorted(self, default_units: MeshUnits):
        """Test that unsorted splits are handled correctly."""
        config = HeightmapSplittingConfig(enabled=True, splits_x=[75.0, 25.0, 50.0])
        splitter = HeightmapSplitter(config, default_units)

        heightmap = np.zeros((100, 100))
        tiles = splitter.split_heightmap(heightmap)

        # Should create 4 tiles (3 splits)
        assert len(tiles) == 4

        # Tiles should be in correct order
        r0c0 = next(t for t in tiles if t.tile_id == "r0c0")
        r0c1 = next(t for t in tiles if t.tile_id == "r0c1")
        r0c2 = next(t for t in tiles if t.tile_id == "r0c2")
        r0c3 = next(t for t in tiles if t.tile_id == "r0c3")

        assert r0c0.col_offset == 0
        assert r0c1.col_offset == 25
        assert r0c2.col_offset == 50
        assert r0c3.col_offset == 75

    def test_preserves_data_values(self, default_units: MeshUnits):
        """Test that tile data is a proper copy with correct values."""
        config = HeightmapSplittingConfig(
            enabled=True, splits_x=[50.0], splits_y=[50.0]
        )
        splitter = HeightmapSplitter(config, default_units)

        # Create heightmap with known pattern
        heightmap = np.arange(10000).reshape(100, 100).astype(float)
        tiles = splitter.split_heightmap(heightmap)

        # Top-left tile should start with 0
        r0c0 = next(t for t in tiles if t.tile_id == "r0c0")
        assert r0c0.data[0, 0] == 0.0

        # Bottom-right tile should end with 9999
        r1c1 = next(t for t in tiles if t.tile_id == "r1c1")
        assert r1c1.data[-1, -1] == 9999.0

    def test_empty_splits_no_splitting(self, default_units: MeshUnits):
        """Test that empty split lists result in no splitting."""
        config = HeightmapSplittingConfig(enabled=True, splits_x=[], splits_y=[])
        splitter = HeightmapSplitter(config, default_units)

        heightmap = np.zeros((100, 100))
        tiles = splitter.split_heightmap(heightmap)

        # No splits = 1 tile
        assert len(tiles) == 1
        assert tiles[0].tile_id == "r0c0"
