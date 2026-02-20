"""Scipy-based triangulator using Delaunay triangulation."""

import logging
from dataclasses import dataclass
from typing import List, Tuple, Union

import numpy as np
from bathy.config import MeshGenerationConfig
from scipy.spatial import Delaunay
from shapely.geometry import MultiPolygon, Point, Polygon

logger = logging.getLogger(__name__)


@dataclass
class TriangulationResult:
    """Result of polygon triangulation with boundary information.

    Attributes:
        vertices: (N, 2) array of 2D vertex coordinates
        triangles: (M, 3) array of triangle vertex indices
        exterior_vertex_count: Number of vertices in the exterior ring (indices 0 to N-1)
        hole_vertex_counts: List of vertex counts for each hole ring

    The vertex array is ordered as:
        [exterior vertices (0..exterior_count-1)]
        [hole 1 vertices (exterior_count..exterior_count+hole1_count-1)]
        [hole 2 vertices (...)]
        ...
        [interior points (after all boundary vertices)]
    """

    vertices: np.ndarray
    triangles: np.ndarray
    exterior_vertex_count: int
    hole_vertex_counts: list[int]

    @property
    def total_boundary_vertices(self) -> int:
        """Total number of boundary vertices (exterior + all holes)."""
        return self.exterior_vertex_count + sum(self.hole_vertex_counts)

    def get_exterior_indices(self) -> list[int]:
        """Get vertex indices for the exterior ring."""
        return list(range(self.exterior_vertex_count))

    def get_hole_indices(self, hole_index: int) -> list[int]:
        """Get vertex indices for a specific hole ring."""
        if hole_index < 0 or hole_index >= len(self.hole_vertex_counts):
            raise ValueError(f"Invalid hole index: {hole_index}")

        start = self.exterior_vertex_count + sum(self.hole_vertex_counts[:hole_index])
        end = start + self.hole_vertex_counts[hole_index]
        return list(range(start, end))


@dataclass
class Triangulator:
    """
    Handles polygon triangulation using scipy.spatial.Delaunay.

    Boundary vertices are guaranteed to be at the start of the vertex array
    in a predictable order (exterior first, then holes), enabling reliable
    side face generation.
    """

    add_interior_points: bool = True
    interior_point_density: float = 1.0

    @classmethod
    def from_config(cls, config: MeshGenerationConfig) -> "Triangulator":
        """Create Triangulator from configuration."""
        return Triangulator(
            add_interior_points=config.triangulation.triangulator_add_interior_points,
            interior_point_density=config.triangulation.triangulator_interior_point_density,
        )

    def triangulate_polygon(
        self, geometries: Union[Polygon, MultiPolygon, List[Polygon]]
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Triangulate polygon geometries using scipy Delaunay triangulation.

        Args:
            geometries: Single polygon, MultiPolygon, or list of polygons to triangulate

        Returns:
            Tuple of (vertices, triangles) where:
            - vertices: (N, 2) array of 2D vertex coordinates
            - triangles: (M, 3) array of triangle vertex indices

        Raises:
            ValueError: If geometries are invalid or triangulation fails
        """
        result = self.triangulate_polygon_with_info(geometries)
        return result.vertices, result.triangles

    def triangulate_polygon_with_info(
        self, geometries: Union[Polygon, MultiPolygon, List[Polygon]]
    ) -> TriangulationResult:
        """
        Triangulate polygon geometries and return detailed boundary information.

        Args:
            geometries: Single polygon, MultiPolygon, or list of polygons to triangulate

        Returns:
            TriangulationResult with vertices, triangles, and boundary index information

        Raises:
            ValueError: If geometries are invalid or triangulation fails
        """
        polygons = self._normalize_geometries(geometries)

        # For now, handle single polygon - future enhancement for multiple polygons
        if len(polygons) != 1:
            raise ValueError("Multiple polygon triangulation not yet implemented")

        polygon = polygons[0]
        return self._triangulate_single_polygon(polygon)

    def _triangulate_single_polygon(self, polygon: Polygon) -> TriangulationResult:
        """
        Triangulate a single Shapely polygon using scipy Delaunay.

        Boundary vertices are placed at the start of the vertex array in order:
        1. Exterior ring vertices (indices 0 to exterior_count-1)
        2. Hole ring vertices (in order of polygon.interiors)
        3. Interior points (if enabled)

        Args:
            polygon: Shapely Polygon object to triangulate

        Returns:
            TriangulationResult with vertices, triangles, and boundary information

        Raises:
            ValueError: If polygon is invalid or triangulation fails
        """
        if not polygon.is_valid:
            raise ValueError("Input polygon is not valid")

        if polygon.area == 0:
            raise ValueError("Input polygon has zero area")

        # Extract boundary points with counts
        exterior_coords = np.array(polygon.exterior.coords[:-1])
        exterior_count = len(exterior_coords)

        hole_coords_list = []
        hole_counts = []
        for interior in polygon.interiors:
            coords = np.array(interior.coords[:-1])
            hole_coords_list.append(coords)
            hole_counts.append(len(coords))

        # Build vertex array: exterior first, then holes, then interior points
        boundary_points = [exterior_coords]
        boundary_points.extend(hole_coords_list)
        all_boundary = (
            np.vstack(boundary_points) if boundary_points else np.empty((0, 2))
        )

        total_boundary_count = len(all_boundary)

        # Optionally add interior points for better triangulation
        if self.add_interior_points:
            interior_points = self._generate_interior_points(polygon)
            if len(interior_points) == 0:
                logger.warning(
                    "No interior points generated; using boundary points only"
                )
                all_points = all_boundary
            else:
                all_points = np.vstack([all_boundary, interior_points])
        else:
            all_points = all_boundary

        # Perform Delaunay triangulation
        logger.debug(
            f"Triangulating polygon with {len(all_points)} points "
            f"({total_boundary_count} boundary [{exterior_count} exterior, "
            f"{total_boundary_count - exterior_count} hole], "
            f"{len(all_points) - total_boundary_count} interior)"
        )

        try:
            delaunay = Delaunay(all_points)

            # Filter triangles to keep only those inside the polygon
            valid_triangles = self._filter_interior_triangles(
                all_points, delaunay.simplices, polygon
            )

            return TriangulationResult(
                vertices=all_points,
                triangles=valid_triangles,
                exterior_vertex_count=exterior_count,
                hole_vertex_counts=hole_counts,
            )

        except Exception as e:
            raise ValueError(f"Delaunay triangulation failed: {e}") from e

    def _generate_interior_points(self, polygon: Polygon) -> np.ndarray:
        """
        Generate interior points for better triangulation quality.

        Args:
            polygon: Shapely Polygon object

        Returns:
            Array of interior points (N, 2)
        """
        # Get polygon bounds
        minx, miny, maxx, maxy = polygon.bounds
        area = polygon.area

        if area == 0:
            logger.warning("Polygon has zero area; no interior points generated")
            return np.empty((0, 2))

        # Estimate number of interior points based on area and density
        # Use a simple grid-based approach
        target_area_per_point = area / (self.interior_point_density * 100)
        grid_spacing = np.sqrt(target_area_per_point)

        # Generate grid points
        x_points = np.arange(minx + grid_spacing / 2, maxx, grid_spacing)
        y_points = np.arange(miny + grid_spacing / 2, maxy, grid_spacing)

        interior_points = []
        for x in x_points:
            for y in y_points:
                point = Point(float(x), float(y))
                if polygon.contains(point):
                    interior_points.append([x, y])

        if not interior_points:
            logger.warning(
                "No interior points generated - triangulation may be poor quality"
            )
            return np.empty((0, 2))

        logger.debug(f"Generated {len(interior_points)} interior points")
        return np.array(interior_points)

    def _filter_interior_triangles(
        self, points: np.ndarray, triangles: np.ndarray, polygon: Polygon
    ) -> np.ndarray:
        """
        Filter triangles to keep only those inside the polygon.

        Args:
            points: All triangulation points (N, 2)
            triangles: All triangles from Delaunay (M, 3)
            polygon: Original polygon for containment testing

        Returns:
            Filtered triangles that are inside the polygon
        """
        valid_triangles = []

        for triangle in triangles:
            # Get triangle vertices
            tri_points = points[triangle]

            # Check if triangle centroid is inside polygon
            centroid_x = np.mean(tri_points[:, 0])
            centroid_y = np.mean(tri_points[:, 1])
            centroid = Point(centroid_x, centroid_y)  # type: ignore

            if polygon.contains(centroid):
                valid_triangles.append(triangle)

        if not valid_triangles:
            raise ValueError("No valid triangles found inside polygon")

        logger.debug(
            f"Filtered {len(triangles)} triangles to {len(valid_triangles)} "
            f"interior triangles"
        )

        return np.array(valid_triangles)

    def _normalize_geometries(
        self, geometries: Union[Polygon, MultiPolygon, List[Polygon]]
    ) -> List[Polygon]:
        """
        Normalize input geometries to a list of polygons.

        Args:
            geometries: Input geometries in various formats

        Returns:
            List of Polygon objects

        Raises:
            ValueError: If input contains invalid geometries
        """
        if isinstance(geometries, Polygon):
            return [geometries]
        elif isinstance(geometries, MultiPolygon):
            return list(geometries.geoms)
        elif isinstance(geometries, list):
            for geom in geometries:
                if not isinstance(geom, Polygon):
                    raise ValueError(f"Expected Polygon, got {type(geom)}")
            return geometries
        else:
            raise ValueError(f"Unsupported geometry type: {type(geometries)}")
