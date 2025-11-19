"""Visualization utilities for bathymesh."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Union

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from shapely.geometry import Polygon

from bathymesh.mesh_generator import ThresholdSnapshot

logger = logging.getLogger(__name__)


class Visualizer:
    """Handles visualization of mesh generation steps."""

    def __init__(self, output_dir: Optional[Union[str, Path]] = None):
        self.output_dir = Path(output_dir) if output_dir else None
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

    def plot_contours(
        self,
        snapshots: Dict[int, ThresholdSnapshot],
        title: str = "Extracted Contours",
        filename: Optional[str] = None,
        cmap: str = "viridis",
    ) -> None:
        """
        Plot contours from threshold snapshots.

        Args:
            snapshots: Dictionary mapping level index to ThresholdSnapshot
            title: Plot title
            filename: Output filename (relative to output_dir)
            cmap: Colormap name
        """
        if not snapshots:
            logger.warning("No snapshots provided for plotting")
            return

        fig, ax = plt.subplots(figsize=(10, 10))

        max_idx = max(snapshots.keys())
        
        # Sort by level to ensure consistent plotting order
        sorted_levels = sorted(snapshots.keys())

        for idx in sorted_levels:
            snap = snapshots[idx]
            if not snap.contours:
                continue
                
            gdf = gpd.GeoDataFrame(geometry=snap.contours)
            gdf["level"] = idx
            gdf.plot(
                ax=ax,
                alpha=0.5,
                edgecolor="black",
                label=f"Threshold {idx}",
                cmap=cmap,
                vmin=0,
                vmax=max_idx,
                legend=True,
            )

        ax.set_title(title)
        ax.set_xlabel("X Coordinate")
        ax.set_ylabel("Y Coordinate")
        
        # Handle legend - only show unique labels if too many
        # For now, just let geopandas handle it or simplify if needed
        
        plt.grid(True)

        if filename and self.output_dir:
            save_path = self.output_dir / filename
            plt.savefig(save_path)
            logger.info(f"Saved contour plot to {save_path}")
            plt.close(fig)
        else:
            plt.show()

    def plot_contour_stack(
        self,
        snapshots: Dict[int, ThresholdSnapshot],
        title: str = "Contour Stack",
        filename: Optional[str] = None,
    ) -> None:
        """
        Plot contours in a 3D stack visualization.
        
        Args:
            snapshots: Dictionary mapping level index to ThresholdSnapshot
            title: Plot title
            filename: Output filename
        """
        if not snapshots:
            return

        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')

        sorted_levels = sorted(snapshots.keys())
        
        for idx in sorted_levels:
            snap = snapshots[idx]
            if not snap.contours:
                continue
                
            # Calculate Z height for this level (assuming simple index-based spacing for viz)
            # In a real scenario, we might want the actual physical height from the config
            z_height = idx 

            for poly in snap.contours:
                if poly.is_empty:
                    continue
                    
                # Extract exterior coords
                x, y = poly.exterior.xy
                z = np.full_like(x, z_height)
                ax.plot(x, y, z, color=plt.cm.viridis(idx / len(sorted_levels)), alpha=0.7)
                
                # Handle interiors (holes)
                for interior in poly.interiors:
                    xi, yi = interior.xy
                    zi = np.full_like(xi, z_height)
                    ax.plot(xi, yi, zi, color='red', alpha=0.5, linestyle='--')

        ax.set_title(title)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Level Index")

        if filename and self.output_dir:
            save_path = self.output_dir / filename
            plt.savefig(save_path)
            logger.info(f"Saved contour stack plot to {save_path}")
            plt.close(fig)
        else:
            plt.show()
