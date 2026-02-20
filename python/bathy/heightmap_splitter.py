"""Heightmap splitting functionality for dividing heightmaps into tiles."""

import logging
from dataclasses import dataclass
from typing import Iterator, Union

import numpy as np

from bathy.config import HeightmapSplittingConfig, MeshGenerationConfig, MeshUnits

logger = logging.getLogger(__name__)


@dataclass
class HeightmapTile:
    """A tile of heightmap data with position information.

    Attributes:
        data: 2D numpy array of heightmap values for this tile
        row_index: Tile row index (0 = top)
        col_index: Tile column index (0 = left)
        row_offset: Pixel offset from original heightmap top
        col_offset: Pixel offset from original heightmap left
        mesh_offset_x: X offset in mesh coordinates for positioning
        mesh_offset_y: Y offset in mesh coordinates for positioning
    """

    data: np.ndarray
    row_index: int
    col_index: int
    row_offset: int
    col_offset: int
    mesh_offset_x: float
    mesh_offset_y: float

    @property
    def tile_id(self) -> str:
        """Get a unique identifier for this tile (e.g., 'r0c1')."""
        return f"r{self.row_index}c{self.col_index}"

    @property
    def shape(self) -> tuple[int, int]:
        """Get the shape of this tile's data."""
        return self.data.shape


class HeightmapSplitter:
    """
    Splits heightmap data into tiles for separate mesh generation.

    Split locations are specified in output mesh coordinates (after scaling
    by MeshUnits). The splitter converts these to pixel indices internally.

    Uses absolute values of mesh units for conversion, so negative scale
    factors (used for axis flipping) work correctly with positive split
    locations.
    """

    config: HeightmapSplittingConfig
    mesh_units: MeshUnits

    def __init__(
        self,
        config: HeightmapSplittingConfig,
        mesh_units: Union[MeshUnits, None] = None,
    ) -> None:
        """Initialize HeightmapSplitter.

        Args:
            config: Splitting configuration with split locations
            mesh_units: Mesh scaling units for coordinate conversion.
                        If None, defaults to MeshUnits(1.0, 1.0, 1.0).
        """
        self.config = config
        self.mesh_units = mesh_units if mesh_units is not None else MeshUnits()

    @classmethod
    def from_config(cls, config: MeshGenerationConfig) -> "HeightmapSplitter":
        """Create HeightmapSplitter from MeshGenerationConfig."""
        return cls(
            config.heightmap_splitting,
            config.heightmap_processing.mesh_units,
        )

    def split_heightmap(self, heightmap: np.ndarray) -> list[HeightmapTile]:
        """
        Split a heightmap into tiles based on split locations.

        Args:
            heightmap: 2D numpy array of heightmap values

        Returns:
            List of HeightmapTile objects
        """
        if not self.config.enabled:
            # Return single tile containing entire heightmap
            return [
                HeightmapTile(
                    data=heightmap,
                    row_index=0,
                    col_index=0,
                    row_offset=0,
                    col_offset=0,
                    mesh_offset_x=0.0,
                    mesh_offset_y=0.0,
                )
            ]

        height, width = heightmap.shape

        # Convert split locations from mesh units to pixel indices
        pixel_splits_x = self._mesh_to_pixel_splits(
            self.config.splits_x, width, abs(self.mesh_units.units_x)
        )
        pixel_splits_y = self._mesh_to_pixel_splits(
            self.config.splits_y, height, abs(self.mesh_units.units_y)
        )

        # Create column and row boundaries (including 0 and max)
        col_boundaries = [0] + pixel_splits_x + [width]
        row_boundaries = [0] + pixel_splits_y + [height]

        # Calculate mesh boundaries for offset calculation
        mesh_boundaries_x = (
            [0.0]
            + sorted(self.config.splits_x)
            + [width * abs(self.mesh_units.units_x)]
        )
        mesh_boundaries_y = (
            [0.0]
            + sorted(self.config.splits_y)
            + [height * abs(self.mesh_units.units_y)]
        )

        num_cols = len(col_boundaries) - 1
        num_rows = len(row_boundaries) - 1

        logger.info(
            f"Splitting heightmap ({width}x{height}) into {num_cols}x{num_rows} tiles "
            f"(splits_x={self.config.splits_x}, splits_y={self.config.splits_y})"
        )

        tiles = []
        for row in range(num_rows):
            for col in range(num_cols):
                row_start = row_boundaries[row]
                row_end = row_boundaries[row + 1]
                col_start = col_boundaries[col]
                col_end = col_boundaries[col + 1]

                # Extract tile data
                tile_data = heightmap[row_start:row_end, col_start:col_end].copy()

                # Calculate mesh offset (position of this tile in mesh coordinates)
                mesh_offset_x = mesh_boundaries_x[col]
                mesh_offset_y = mesh_boundaries_y[row]

                tile = HeightmapTile(
                    data=tile_data,
                    row_index=row,
                    col_index=col,
                    row_offset=row_start,
                    col_offset=col_start,
                    mesh_offset_x=mesh_offset_x,
                    mesh_offset_y=mesh_offset_y,
                )
                tiles.append(tile)

                logger.debug(
                    f"Created tile {tile.tile_id}: shape={tile.shape}, "
                    f"pixel_offset=({tile.col_offset}, {tile.row_offset}), "
                    f"mesh_offset=({tile.mesh_offset_x:.1f}, {tile.mesh_offset_y:.1f})"
                )

        logger.info(f"Split heightmap into {len(tiles)} tiles")
        return tiles

    def _mesh_to_pixel_splits(
        self, mesh_splits: list[float], dimension_pixels: int, units_per_pixel: float
    ) -> list[int]:
        """
        Convert mesh-coordinate split locations to pixel indices.

        Args:
            mesh_splits: Split locations in mesh units
            dimension_pixels: Total pixels in this dimension
            units_per_pixel: Mesh units per pixel (absolute value)

        Returns:
            Sorted list of unique pixel indices for splits
        """
        if not mesh_splits or units_per_pixel == 0:
            return []

        pixel_splits = []
        for mesh_pos in mesh_splits:
            # Convert mesh position to pixel index
            pixel_idx = int(mesh_pos / units_per_pixel)

            # Clamp to valid range (exclude 0 and max as they're implicit boundaries)
            if 0 < pixel_idx < dimension_pixels:
                pixel_splits.append(pixel_idx)
            else:
                logger.warning(
                    f"Split at mesh position {mesh_pos} maps to pixel {pixel_idx}, "
                    f"which is outside valid range (1, {dimension_pixels - 1}). Skipping."
                )

        # Sort and remove duplicates
        return sorted(set(pixel_splits))

    def iter_tiles(self, heightmap: np.ndarray) -> Iterator[HeightmapTile]:
        """
        Iterate over tiles of a heightmap.

        This is a memory-efficient alternative to split_heightmap() that
        yields tiles one at a time.

        Args:
            heightmap: 2D numpy array of heightmap values

        Yields:
            HeightmapTile objects
        """
        for tile in self.split_heightmap(heightmap):
            yield tile

    def get_tile_count(
        self, heightmap_shape: Union[tuple[int, int], None] = None
    ) -> int:
        """Get the total number of tiles that will be generated.

        Args:
            heightmap_shape: Optional (height, width) tuple. If provided,
                            validates splits against dimensions.

        Returns:
            Number of tiles
        """
        if not self.config.enabled:
            return 1

        # Number of tiles = (number of splits + 1) for each axis
        num_cols = len(self.config.splits_x) + 1
        num_rows = len(self.config.splits_y) + 1

        return num_cols * num_rows

    def get_grid_dimensions(self) -> tuple[int, int]:
        """Get the tile grid dimensions (rows, cols).

        Returns:
            Tuple of (num_rows, num_cols)
        """
        if not self.config.enabled:
            return (1, 1)

        num_cols = len(self.config.splits_x) + 1
        num_rows = len(self.config.splits_y) + 1

        return (num_rows, num_cols)
