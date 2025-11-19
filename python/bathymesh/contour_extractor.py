"""Heightmap processing functionality for bathymesh."""

import logging
from dataclasses import dataclass, field
from typing import List, Union

import cv2
import numpy as np
from shapely.geometry import Polygon
from shapely.ops import unary_union
from skimage import measure

from bathymesh.config import ContourParams

logger = logging.getLogger(__name__)


@dataclass
class ContourExtractor:
    """Processes 2D heightmaps to extract contours and generate polygons."""

    config: ContourParams = field(default_factory=ContourParams)

    def extract_contour_polygons(
        self,
        heightmap: np.ndarray,
        threshold: float,
    ) -> List[Polygon]:
        """
        Extract true horizontal slice polygons at threshold, handling nested contours.

        This method correctly handles cases where heightmaps have peaks and valleys
        by creating polygons with holes where appropriate. For example, a circular
        peak will produce an outer contour (going up) and inner contour (going down),
        and the result is a ring-shaped polygon.

        Args:
            heightmap: 2D numpy array of height values
            threshold: Height threshold for contour extraction
            simplify_tolerance: Initial tolerance for Douglas-Peucker simplification
            max_segments: Maximum segments per polygon before increasing simplification
            min_area_fraction: Minimum area as fraction of largest polygon

        Returns:
            List of valid Shapely Polygon objects (potentially with holes)

        Raises:
            ValueError: If heightmap is not 2D or threshold is invalid
        """
        if heightmap.ndim != 2:
            raise ValueError(f"Heightmap must be 2D, got {heightmap.ndim}D")

        logger.debug(f"Extracting contours with OpenCV at threshold {threshold}")

        # Create binary mask
        mask = (heightmap >= threshold).astype(np.uint8)

        # Find contours with hierarchy
        # RETR_CCOMP: retrieves all contours and organizes them into 2-level hierarchy
        # - External contours at hierarchy level 0
        # - Holes at hierarchy level 1
        contours_cv, hierarchy = cv2.findContours(
            mask, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_SIMPLE
        )

        if len(contours_cv) == 0:
            logger.warning(f"No contours found at threshold {threshold}")
            return []

        logger.info(f"Found {len(contours_cv)} contours with OpenCV")

        # hierarchy shape: [Next, Previous, First_Child, Parent]
        # For RETR_CCOMP:
        # - If Parent == -1, it's an external contour
        # - If Parent >= 0, it's a hole of that parent
        hierarchy = hierarchy[0]  # Remove extra dimension

        try:
            contours = measure.find_contours(mask.astype(float), 0.5)
        except Exception as e:
            raise ValueError(f"Failed to extract contours: {e}") from e

        # Convert contours to polygons
        all_raw_polygons = []
        for i, contour in enumerate(contours):
            try:
                polygon = self._contour_to_polygon(contour)
                if (
                    polygon
                    and polygon.is_valid
                    and polygon.area > self.config.min_polygon_area
                ):
                    all_raw_polygons.append(polygon)
                    logger.debug(f"Added raw polygon {i} with area {polygon.area:.3f}")
            except Exception as e:
                logger.warning(f"Failed to process contour {i}: {e}")
                continue
        # Build polygons with holes
        result_polygons = []
        processed = set()

        for i, contour_cv in enumerate(contours_cv):
            if i in processed:
                continue

            # Check if this is an external contour (not a hole)
            parent_idx = hierarchy[i][3]
            if parent_idx != -1:
                # This is a hole, will be processed with its parent
                continue

            # Convert external contour to polygon
            try:
                # OpenCV contours: shape (n, 1, 2), need to reshape
                coords = contour_cv.squeeze()
                if len(coords) < 3:
                    continue

                # Flip y-axis to match numpy convention
                coords = coords[:, [0, 1]]  # x, y order

                exterior_poly = Polygon(coords)

                if (
                    not exterior_poly.is_valid
                    or exterior_poly.area < self.config.min_polygon_area
                ):
                    continue

                # Find holes (children of this contour)
                holes = []
                first_child = hierarchy[i][2]

                if first_child != -1:
                    # Process child and its siblings
                    child_idx = first_child
                    while child_idx != -1:
                        hole_contour = contours_cv[child_idx].squeeze()
                        if len(hole_contour) >= 3:
                            hole_coords = hole_contour[:, [0, 1]]
                            holes.append(hole_coords)
                            processed.add(child_idx)

                        # Move to next sibling
                        child_idx = hierarchy[child_idx][0]

                # Create polygon with holes
                if holes:
                    try:
                        poly_with_holes = Polygon(coords, holes=holes)
                        result_polygons.append(poly_with_holes)
                        logger.debug(f"Created polygon {i} with {len(holes)} holes")
                    except Exception as e:
                        logger.warning(f"Failed to create polygon with holes: {e}")
                        result_polygons.append(exterior_poly)
                else:
                    result_polygons.append(exterior_poly)

                processed.add(i)

            except Exception as e:
                logger.warning(f"Failed to process contour {i}: {e}")
                continue

        logger.info(f"Built {len(result_polygons)} polygons with OpenCV")

        # use result polygons as invert bool cut for unary union

        full_union = unary_union(all_raw_polygons)
        holes_removed = full_union.difference(unary_union(result_polygons))

        if isinstance(holes_removed, Polygon):
            result_polygons = [holes_removed]
        else:
            result_polygons = list(holes_removed.geoms)  # type: ignore

        # Filter and simplify
        result_polygons = self._filter_and_simplify_polygons(
            result_polygons,
            self.config.simplify_tolerance,
            self.config.max_segments,
            self.config.min_area_fraction,
        )

        logger.info(
            f"Final polygon count after filtering and simplification: {len(result_polygons)}"
        )
        for poly in result_polygons:
            if not poly.is_valid:
                logger.warning("Invalid polygon found after processing")

        # Remove interior geometries if they occupy >= 95% of total area
        cleaned_polygons = []
        for poly in result_polygons:
            if len(poly.interiors) > 0:
                # Calculate total hole area
                hole_area = sum(Polygon(interior).area for interior in poly.interiors)
                total_area = poly.area

                # If holes take up 95% or more, create polygon without holes
                if hole_area >= 0.95 * total_area:
                    cleaned_poly = Polygon(poly.exterior.coords)
                    cleaned_polygons.append(cleaned_poly)
                    logger.warning(
                        f"Removed interiors from polygon (hole area {hole_area:.2f} >= 95% of {total_area:.2f})"
                    )
                else:
                    cleaned_polygons.append(poly)
            else:
                cleaned_polygons.append(poly)

        result_polygons = cleaned_polygons

        return result_polygons

    def _filter_and_simplify_polygons(
        self,
        polygons: List[Polygon],
        simplify_tolerance: float,
        max_segments: int,
        min_area_fraction: float,
    ) -> List[Polygon]:
        """
        Filter and simplify polygons based on area and segment count.

        Args:
            polygons: List of polygons to filter and simplify
            simplify_tolerance: Initial tolerance for simplification
            max_segments: Maximum segments per polygon
            min_area_fraction: Minimum area as fraction of largest polygon

        Returns:
            Filtered and simplified list of polygons
        """
        if not polygons:
            return []

        # Filter by area
        max_area = max(p.area for p in polygons)
        area_threshold = max_area * min_area_fraction
        result = [p for p in polygons if p.area >= area_threshold]
        logger.info(
            f"Filtered to {len(result)} polygons with area >= {area_threshold:.3f}"
        )

        if not result:
            return []

        # Simplify if needed
        tolerance = simplify_tolerance
        while result:
            max_seg = max(len(p.exterior.coords) for p in result)
            if max_seg <= max_segments:
                break
            tolerance += 0.1
            result = [p.simplify(tolerance, preserve_topology=True) for p in result]
            logger.info(
                f"Simplified with tolerance {tolerance:.3f}, max segments now {max_seg}"
            )

        return result  # type: ignore

    def _contour_to_polygon(self, contour: np.ndarray) -> Union[Polygon, None]:
        """
        Convert contour to Shapely polygon.

        Args:
            contour: Contour coordinates from skimage

        Returns:
            Shapely Polygon or None if conversion fails
        """
        if len(contour) < 3:
            return None

        # Flip axis to get (x, y) instead of (row, col)
        coords = np.flip(contour, axis=1)

        try:
            return Polygon(coords)
        except Exception:
            return None
