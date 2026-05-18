from pathlib import Path
from typing import Union

import geopandas as gpd
from bathy.mesh_generator import MeshGenerator
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure

import logging

logger = logging.getLogger(__name__)


def contour_plot(
    generator: MeshGenerator, save_path: Union[None, Path]
) -> tuple[Figure, Axes]:

    # Plot Contours
    fig, ax = plt.subplots(figsize=(10, 10))

    max_idx = max(generator.threshold_snapshots.keys())
    for idx, snap in generator.threshold_snapshots.items():
        contours = snap.contours
        gdf = gpd.GeoDataFrame(geometry=contours)
        gdf["level"] = idx

        if len(gdf) == 0:
            logger.warning(
                f"No contours found for threshold {idx}, skipping plot for this level"
            )
            logger.warning(contours)
            continue

        gdf.plot(
            ax=ax,
            alpha=0.5,
            edgecolor="black",
            label=f"Threshold {idx}",
            cmap="viridis",
            vmin=0,
            vmax=max_idx,
            legend=True,
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
