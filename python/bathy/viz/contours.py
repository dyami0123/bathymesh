import logging
from pathlib import Path
from typing import Union

import geopandas as gpd
import matplotlib
import matplotlib.colors
from bathy.mesh_generator import MeshGenerator
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from shapely import affinity

logger = logging.getLogger(__name__)


def contour_plot(
    generator: MeshGenerator, save_path: Union[None, Path], vmax: float = 1
) -> tuple[Figure, Axes]:
    """
    Plot contours extracted during mesh generation.

    Supports both single-tile mode (using threshold_snapshots) and multi-tile
    mode (using tile_snapshots with offsets for proper positioning).

    Args:
        generator: MeshGenerator with populated snapshots
        save_path: Path to save the plot (or None to skip saving)
        vmax: Maximum value for colormap normalization

    Returns:
        Tuple of (Figure, Axes)
    """
    fig, ax = plt.subplots(figsize=(10, 10))

    # Check if we have multi-tile snapshots
    if generator.tile_snapshots:
        _plot_multi_tile_contours(generator, ax, vmax)
    elif generator.threshold_snapshots:
        _plot_single_tile_contours(generator, ax, vmax)
    else:
        logger.warning("No contour snapshots available to plot")
        ax.text(
            0.5,
            0.5,
            "No contour data available",
            ha="center",
            va="center",
            transform=ax.transAxes,
        )

    ax.set_title("Extracted Contours at Different Height Thresholds")
    ax.set_xlabel("X Coordinate")
    ax.set_ylabel("Y Coordinate")
    ax.legend(title="Height Thresholds")
    plt.grid(True)

    if save_path:
        save_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path)

    return fig, ax


def _plot_single_tile_contours(generator: MeshGenerator, ax: Axes, vmax: float) -> None:
    """
    Plot contours from single-tile mode (threshold_snapshots).

    Args:
        generator: MeshGenerator with threshold_snapshots
        ax: Matplotlib axes to plot on
        vmax: Maximum value for colormap normalization
    """
    max_idx = max(generator.threshold_snapshots.keys())
    cmap = plt.get_cmap("viridis")
    norm = matplotlib.colors.Normalize(vmin=0, vmax=max_idx)

    for idx, snap in generator.threshold_snapshots.items():
        contours = snap.contours
        if (contours is None) or (len(contours) == 0):
            logger.warning(f"No contours found for threshold {idx}")
            continue

        gdf = gpd.GeoDataFrame(geometry=contours)
        gdf.geometry = gdf.geometry.rotate(180, origin=(0, 0))
        gdf["level"] = idx / max_idx * vmax

        gdf.plot(
            "level",
            ax=ax,
            alpha=0.5,
            edgecolor="black",
            label=f"Threshold {idx}",
            cmap="viridis",
            vmin=0,
            vmax=vmax,
            legend=idx == 1,
        )

        # Add labels for the first 3 geometries at their centroid
        color = cmap(norm(idx))
        _add_centroid_labels(gdf, ax, idx, color, max_labels=3)


def _plot_multi_tile_contours(generator: MeshGenerator, ax: Axes, vmax: float) -> None:
    """
    Plot contours from multi-tile mode (tile_snapshots with offsets).

    Combines contours from all tiles into a single plot by translating
    each tile's contours by its mesh offset.

    Args:
        generator: MeshGenerator with tile_snapshots and tile_offsets
        ax: Matplotlib axes to plot on
        vmax: Maximum value for colormap normalization
    """
    # Find the maximum level index across all tiles for normalization
    max_idx = 0
    for tile_snaps in generator.tile_snapshots.values():
        if tile_snaps:
            max_idx = max(max_idx, max(tile_snaps.keys()))

    if max_idx == 0:
        logger.warning("No valid levels found in tile snapshots")
        return

    cmap = plt.get_cmap("viridis")
    norm = matplotlib.colors.Normalize(vmin=0, vmax=max_idx)

    # Track which levels we've added to legend
    levels_in_legend: set[int] = set()

    for tile_id, tile_snaps in generator.tile_snapshots.items():
        # Get offset for this tile
        offset_x, offset_y = generator.tile_offsets.get(tile_id, (0.0, 0.0))
        
        if generator.config.heightmap_processing.mesh_units.units_x < 0:
            offset_x = -offset_x
        
        if generator.config.heightmap_processing.mesh_units.units_y < 0:
            offset_y = -offset_y

        for idx, snap in tile_snaps.items():
            contours = snap.contours
            if (contours is None) or (len(contours) == 0):
                continue

            # Translate contours by tile offset
            translated_contours = [
                affinity.translate(geom, xoff=offset_x, yoff=offset_y)
                for geom in contours
            ]

            gdf = gpd.GeoDataFrame(geometry=translated_contours)
            gdf.geometry = gdf.geometry.rotate(180, origin=(0, 0))
            gdf["level"] = idx / max_idx * vmax

            # Only add legend for first occurrence of each level
            show_legend = idx not in levels_in_legend and idx == 1
            if idx not in levels_in_legend:
                levels_in_legend.add(idx)

            gdf.plot(
                "level",
                ax=ax,
                alpha=0.5,
                edgecolor="black",
                label=f"Threshold {idx}" if show_legend else "",
                cmap="viridis",
                vmin=0,
                vmax=vmax,
                legend=show_legend,
            )

            # Add labels for first tile only to avoid clutter
            if tile_id == list(generator.tile_snapshots.keys())[0]:
                color = cmap(norm(idx))
                _add_centroid_labels(gdf, ax, idx, color, max_labels=3)


def _add_centroid_labels(
    gdf: gpd.GeoDataFrame,
    ax: Axes,
    level_idx: int,
    color: tuple,
    max_labels: int = 3,
) -> None:
    """
    Add level labels at polygon centroids.

    Args:
        gdf: GeoDataFrame with geometries
        ax: Matplotlib axes
        level_idx: Level index to display
        color: Text color
        max_labels: Maximum number of labels to add
    """
    for _, geom in enumerate(gdf.geometry[:max_labels]):
        if not geom.is_empty and geom.geom_type in ("Polygon", "MultiPolygon"):
            centroid = geom.centroid
            ax.text(
                centroid.x,
                centroid.y,
                str(level_idx),
                fontsize=9,
                color=color,
                ha="center",
                va="center",
                bbox=dict(
                    facecolor="white",
                    edgecolor="none",
                    alpha=1,
                    boxstyle="round,pad=0.2",
                ),
            )
