import logging
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import open3d as o3d
from shapely.geometry import Polygon
from tqdm import tqdm

from bathymesh.contour_extractor import ContourExtractor
from bathymesh.config import MeshConfig
from bathymesh.data_model import HeightmapData, MeshData
from bathymesh.mesh_combiner import MeshCombiner
from bathymesh.mesh_post_processor import MeshPostProcessor, SimplificationMethod
from bathymesh.triangulator import Triangulator

logger = logging.getLogger(__name__)


@dataclass
class ThresholdSnapshot:
    threshold: float
    mesh: Optional[o3d.geometry.TriangleMesh] = None
    contours: Optional[list[Polygon]] = None
    vertices_2d: Optional[list[np.ndarray]] = None
    triangles: Optional[list[np.ndarray]] = None


@dataclass
class MeshGenerator:
    #############################
    # Mesh Generation Parameters
    #############################

    config: MeshConfig
    stateless: bool = True

    ##############################
    # Object State
    # ##############################

    threshold_snapshots: dict[int, ThresholdSnapshot] = field(default_factory=dict)

    def __init__(self, config: MeshConfig, stateless: bool = True) -> None:
        self.config = config
        self.stateless = stateless

        self.mesh_combiner = MeshCombiner(
            merge_threshold=self.config.combiner.merge_threshold
        )
        self.triangulator = Triangulator(
            add_interior_points=self.config.triangulation.add_interior_points,
            interior_point_density=self.config.triangulation.interior_point_density,
        )
        self.mesh_processor = MeshPostProcessor(
            remove_degenerate_triangles=self.config.post_process.remove_degenerate_triangles,
            remove_duplicated_vertices=self.config.post_process.remove_duplicated_vertices,
            remove_duplicated_triangles=self.config.post_process.remove_duplicated_triangles,
            remove_unreferenced_vertices=self.config.post_process.remove_unreferenced_vertices,
            merge_close_vertices=self.config.post_process.merge_close_vertices,
            merge_vertices_threshold=self.config.post_process.merge_vertices_threshold,
            simplification_method=self.config.post_process.simplification_method,
            target_triangle_count=self.config.post_process.target_triangle_count,
            voxel_size=self.config.post_process.voxel_size,
        )
        self.contour_extractor = ContourExtractor(
            min_polygon_area=self.config.contour.min_polygon_area,
            simplify_tolerance=self.config.contour.simplify_tolerance,
            max_segments=self.config.contour.max_segments,
            min_area_fraction=self.config.contour.min_area_fraction,
        )
        self.threshold_snapshots = {}

    def execute(self, heightmap_data: HeightmapData) -> MeshData:
        """
        Execute the multi-level mesh generation workflow.

        Args:
            data: Input data package or heightmap array

        Returns:
            Result package containing combined mesh and metadata
        """

        logger.info("Starting multi-level mesh generation")
        logger.info(f"Heightmap shape: {heightmap_data.data.shape}")
        logger.info(f"Number of levels: {len(self.config.generation.thresholds)}")

        # Generate meshes for each level
        all_meshes = []

        for level_idx, threshold in enumerate(self.config.generation.thresholds):
            self.threshold_snapshots[level_idx] = ThresholdSnapshot(threshold=threshold)

            level_height = self.config.generation.base_height + (level_idx * self.config.generation.layer_thickness)
            logger.info(
                f"Processing level {level_idx + 1}/{len(self.config.generation.thresholds)} "
                f"at threshold {threshold}, height {level_height}"
            )

            mesh_ls = self.generate_mesh(
                heightmap_data,
                level_idx,
                threshold,
                level_height,
            )

            if self.config.post_process.enabled:
                mesh_ls = [self.mesh_processor.process_mesh(mesh) for mesh in mesh_ls]

            for mesh in mesh_ls:
                if len(mesh.vertices) > 0:
                    all_meshes.append(mesh)
                    logger.info(
                        f"Level {level_idx + 1} mesh created with {len(mesh.vertices)} vertices"
                    )
                else:
                    logger.warning(
                        f"No mesh generated for level {level_idx + 1} at threshold {threshold}"
                    )

            if not self.stateless:
                self.threshold_snapshots[level_idx].mesh = mesh_ls

        combined_mesh = self.mesh_combiner.combine_meshes(all_meshes)
        logger.info(f"Combined {len(all_meshes)} level meshes")

        # Process combined mesh if enabled
        if self.config.post_process.enabled:
            logger.info("Processing combined mesh...")
            combined_mesh = self.mesh_processor.process_mesh(combined_mesh)

        return MeshData(data=combined_mesh)

    def generate_mesh(
        self,
        heightmap_data: HeightmapData,
        level_idx: int,
        threshold: float,
        base_height: float = 0.0,
        thickness: float = 1.0,
    ) -> list[o3d.geometry.TriangleMesh]:
        """
        Generate an extruded 3D mesh from heightmap data.

        Args:
            heightmap_handler: HeightmapHandler containing heightmap data
            base_height: Z-coordinate of the base
            thickness: Extrusion thickness
            use_contours: If True, extract contours at threshold, else use bounding polygon
            threshold: Height threshold for contour extraction (required if use_contours=True)

        Returns:
            Open3D TriangleMesh object

        Raises:
            ValueError: If parameters are invalid or mesh generation fails
        """

        polygons = self.contour_extractor.extract_contour_polygons(
            heightmap_data.data, threshold
        )
        logger.info(
            f"Extracted {len(polygons)} polygons at threshold {threshold} for extruded mesh generation"
        )
        if not polygons:
            logger.warning(
                f"No contours found at threshold {threshold}, using empty polygon"
            )
            polygons = []

        triangles = [
            self._build_extruded_mesh(polygon, base_height, thickness, level_idx)
            for polygon in tqdm(polygons, desc="Generating extruded mesh")
        ]

        logger.info(f"Generated {len(triangles)} extruded mesh(es) from polygons")

        if not self.stateless:
            if level_idx not in self.threshold_snapshots:
                self.threshold_snapshots[level_idx] = ThresholdSnapshot(
                    threshold=threshold
                )

            self.threshold_snapshots[level_idx].contours = polygons
        return triangles

    def _build_extruded_mesh(
        self,
        polygon: Polygon,
        base_height: float,
        thickness: float,
        level_idx: int,
    ) -> o3d.geometry.TriangleMesh:
        """
        Build extruded mesh from triangulated polygon.

        Args:
            vertices_2d: 2D vertices from triangulation
            triangles: Triangle indices
            polygon: Original polygon for boundary extraction
            base_height: Base Z-coordinate
            thickness: Extrusion thickness

        Returns:
            Open3D TriangleMesh object
        """

        vertices_2d, triangles = self.triangulator.triangulate_polygon(polygon)
        n_vertices = len(vertices_2d)

        # Create 3D vertices for bottom and top
        bottom_z = base_height
        top_z = base_height + thickness
        bottom_vertices = np.column_stack((vertices_2d, np.full(n_vertices, bottom_z)))
        top_vertices = np.column_stack((vertices_2d, np.full(n_vertices, top_z)))

        all_vertices = np.vstack((bottom_vertices, top_vertices))

        # Create faces
        bottom_faces = triangles
        top_faces = (
            triangles[:, ::-1] + n_vertices
        )  # Reverse winding and offset indices

        # Create side faces from polygon boundary
        side_faces = self._create_side_faces(vertices_2d, polygon, n_vertices)

        if len(side_faces) == 0:
            logger.warning("No side faces created, mesh may have holes")
            faces = np.vstack((bottom_faces, top_faces))
        else:
            faces = np.vstack((bottom_faces, top_faces, side_faces))

        # Validate face indices
        max_vertex_idx = len(all_vertices) - 1
        if faces.max() > max_vertex_idx:
            raise ValueError(
                f"Invalid face indices: max {faces.max()} > {max_vertex_idx}"
            )

        mesh = self._create_mesh_from_vertices_faces(all_vertices, faces)

        logger.debug(
            f"Created extruded mesh with {len(all_vertices)} vertices and {len(faces)} triangles"
        )

        if not self.stateless:
            snapshot = self.threshold_snapshots.get(level_idx)
            if snapshot:
                if snapshot.vertices_2d is None:
                    snapshot.vertices_2d = []
                if snapshot.triangles is None:
                    snapshot.triangles = []

                snapshot.vertices_2d.append(vertices_2d)
                snapshot.triangles.append(triangles)

        return mesh

    def _create_side_faces(
        self, vertices_2d: np.ndarray, polygon: Polygon, n_vertices: int
    ) -> np.ndarray:
        """
        Create side faces for extruded mesh from polygon boundary.

        Args:
            vertices_2d: 2D vertices from triangulation
            polygon: Original polygon for boundary
            n_vertices: Number of vertices in each layer

        Returns:
            Array of side face indices
        """
        # Extract boundary coordinates
        boundary_coords = np.array(polygon.exterior.coords[:-1])

        # Find triangulated vertices that correspond to boundary points
        boundary_indices = self._map_boundary_to_vertices(boundary_coords, vertices_2d)

        if len(boundary_indices) < 3:
            logger.warning("Insufficient boundary vertices for side faces")
            return np.array([])

        # Create side faces
        side_faces = []
        for i in range(len(boundary_indices)):
            curr_idx = boundary_indices[i]
            next_idx = boundary_indices[(i + 1) % len(boundary_indices)]

            # Validate indices
            if curr_idx >= n_vertices or next_idx >= n_vertices:
                logger.warning(
                    f"Invalid boundary index {curr_idx} or {next_idx}, skipping"
                )
                continue

            # Two triangles for each boundary edge
            side_faces.extend(
                [
                    [curr_idx, next_idx, next_idx + n_vertices],
                    [curr_idx, next_idx + n_vertices, curr_idx + n_vertices],
                ]
            )

        return np.array(side_faces) if side_faces else np.array([])

    def _create_mesh_from_vertices_faces(
        self, vertices: np.ndarray, faces: np.ndarray
    ) -> o3d.geometry.TriangleMesh:
        """
        Create Open3D mesh from vertices and faces.

        Args:
            vertices: (N, 3) array of 3D vertex coordinates
            faces: (M, 3) array of triangle vertex indices

        Returns:
            Open3D TriangleMesh object
        """
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(faces)
        mesh.compute_vertex_normals()
        return mesh

    def _map_boundary_to_vertices(
        self, boundary_coords: np.ndarray, vertices_2d: np.ndarray
    ) -> list[int]:
        """
        Map polygon boundary coordinates to triangulated vertex indices.

        Args:
            boundary_coords: Boundary coordinates from polygon
            vertices_2d: Triangulated vertex coordinates

        Returns:
            List of vertex indices corresponding to boundary
        """
        boundary_indices = []
        for boundary_point in boundary_coords:
            # Find closest vertex in triangulated vertices
            distances = np.sum((vertices_2d - boundary_point) ** 2, axis=1)
            closest_idx = np.argmin(distances)
            boundary_indices.append(closest_idx)

        return boundary_indices
