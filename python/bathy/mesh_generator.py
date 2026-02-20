import logging
from typing import Union

import numpy as np
import open3d as o3d
from bathy.config import MeshGenerationConfig
from bathy.contour_extractor import ContourExtractor
from bathy.data_model import HeightmapData, MeshData, SplitMeshResult, ThresholdSnapshot
from bathy.heightmap_splitter import HeightmapSplitter, HeightmapTile
from bathy.mesh_combiner import MeshCombiner
from bathy.mesh_post_processor import MeshPostProcessor
from bathy.mesh_splitter import MeshSplitter
from bathy.triangulator import Triangulator, TriangulationResult
from shapely.geometry import Polygon
from tqdm import tqdm

logger = logging.getLogger(__name__)


class MeshGenerator:
    config: MeshGenerationConfig
    # Contour Extraction
    contour_extractor: ContourExtractor
    # Combiner
    combiner: MeshCombiner
    # Triangulator
    triangulator: Triangulator

    # PostProcessing
    mesh_processor: MeshPostProcessor

    # Splitting (deprecated - use heightmap_splitter instead)
    mesh_splitter: MeshSplitter

    # Heightmap-based splitting (preferred)
    heightmap_splitter: HeightmapSplitter

    mesh_combiner: MeshCombiner

    # Snapshot tracking for visualization
    threshold_snapshots: dict[
        int, ThresholdSnapshot
    ]  # Single-tile mode: level_idx → snapshot

    # Multi-tile snapshot tracking: tile_id → level_idx → snapshot
    tile_snapshots: dict[str, dict[int, ThresholdSnapshot]]

    # Tile offsets for visualization: tile_id → (mesh_offset_x, mesh_offset_y)
    tile_offsets: dict[str, tuple[float, float]]

    def __init__(self, config: MeshGenerationConfig) -> None:
        self.config = config
        self.contour_extractor = ContourExtractor.from_config(config)
        self.combiner = MeshCombiner.from_config(config)
        self.triangulator = Triangulator.from_config(config)
        self.mesh_processor = MeshPostProcessor.from_config(config)
        self.mesh_splitter = MeshSplitter.from_config(config)
        self.heightmap_splitter = HeightmapSplitter.from_config(config)
        self.mesh_combiner = MeshCombiner.from_config(config)
        self.threshold_snapshots = {}
        self.tile_snapshots = {}
        self.tile_offsets = {}

    def execute(self, heightmap_data: HeightmapData) -> Union[None, SplitMeshResult]:
        """
        Execute the multi-level mesh generation workflow.

        Args:
            heightmap_data: Input heightmap data

        Returns:
            SplitMeshResult containing combined mesh, optional split pieces, and tile info
        """
        logger.info("Starting multi-level mesh generation")
        logger.info(f"Heightmap shape: {heightmap_data.data.shape}")
        logger.info(
            f"Number of levels: {len(self.config.heightmap_processing.thresholds)}"
        )

        # Check if heightmap splitting is enabled
        if self.config.heightmap_splitting.enabled:
            return self._execute_with_tiles(heightmap_data)
        else:
            return self._execute_single(heightmap_data)

    def _execute_single(
        self, heightmap_data: HeightmapData
    ) -> Union[None, SplitMeshResult]:
        """
        Execute mesh generation on a single heightmap (no tiling).

        Args:
            heightmap_data: Input heightmap data

        Returns:
            SplitMeshResult with combined mesh and optional mesh-based splitting
        """
        # Generate meshes for each level
        all_meshes = []

        for level_idx, threshold in enumerate(
            self.config.heightmap_processing.thresholds
        ):
            self.threshold_snapshots[level_idx] = ThresholdSnapshot(threshold=threshold)

            level_height = self.config.heightmap_processing.base_height + (
                level_idx * self.config.heightmap_processing.layer_thickness
            )
            logger.info(
                f"Processing level {level_idx + 1}/{len(self.config.heightmap_processing.thresholds)} "
                f"at threshold {threshold}, height {level_height}"
            )

            mesh_ls = self.generate_mesh(
                heightmap_data,
                level_idx,
                threshold,
                level_height,
            )

            if self.config.post_processing.apply_post_processing:
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

            if not self.config.stateless:
                self.threshold_snapshots[level_idx].mesh = mesh_ls

        combined_mesh = self.mesh_combiner.combine_meshes(all_meshes)

        if combined_mesh is None:
            return None

        logger.info(f"Combined {len(all_meshes)} level meshes")

        # Process combined mesh if enabled
        if self.config.post_processing.apply_post_processing:
            logger.info("Processing combined mesh...")
            combined_mesh = self.mesh_processor.process_mesh(combined_mesh)

        # Mesh splitting (optional, deprecated - use heightmap splitting instead)
        split_meshes: list[o3d.geometry.TriangleMesh] = []
        split_planes: list[
            tuple[tuple[float, float, float], tuple[float, float, float]]
        ] = []

        if self.config.mesh_splitting.enabled:
            logger.info(
                "Splitting mesh (deprecated - consider using heightmap splitting)..."
            )
            split_meshes = self.mesh_splitter.split_mesh(combined_mesh)
            logger.info(f"Split into {len(split_meshes)} sub-meshes")

            # Get planes used for reference
            planes = self.mesh_splitter.get_split_planes(combined_mesh)
            split_planes = [(p.origin, p.normal) for p in planes]

        return SplitMeshResult(
            combined_mesh=combined_mesh,
            split_meshes=split_meshes,
            split_planes=split_planes,
        )

    def _execute_with_tiles(
        self, heightmap_data: HeightmapData
    ) -> Union[None, SplitMeshResult]:
        """
        Execute mesh generation with heightmap-based tiling.

        Splits the heightmap into tiles, generates a complete mesh for each tile,
        and returns all tile meshes.

        Args:
            heightmap_data: Input heightmap data

        Returns:
            SplitMeshResult with tile meshes in split_meshes and tile IDs
        """
        # Clear any previous tile data
        self.tile_snapshots = {}
        self.tile_offsets = {}

        # Split heightmap into tiles
        tiles = self.heightmap_splitter.split_heightmap(heightmap_data.data)
        grid_dims = self.heightmap_splitter.get_grid_dimensions()

        logger.info(
            f"Processing {len(tiles)} tiles ({grid_dims[0]} rows x {grid_dims[1]} cols)"
        )

        tile_meshes: list[o3d.geometry.TriangleMesh] = []
        tile_ids: list[str] = []
        offset_tile_meshes: list[o3d.geometry.TriangleMesh] = []

        for tile in tqdm(tiles, desc="Processing tiles", unit="tile"):
            logger.info(f"Processing tile {tile.tile_id} (shape: {tile.shape})")

            # Store tile offset for visualization
            self.tile_offsets[tile.tile_id] = (tile.mesh_offset_x, tile.mesh_offset_y)

            # Create HeightmapData for this tile
            tile_heightmap = HeightmapData(data=tile.data)

            # Generate mesh for this tile (also populates tile_snapshots)
            tile_mesh = self._generate_tile_mesh(tile_heightmap, tile.tile_id)

            if tile_mesh is None:
                logger.warning(f"No mesh generated for tile {tile.tile_id}")
                continue

            if len(tile_mesh.vertices) > 0:
                # Store untranslated mesh for individual tile export
                tile_meshes.append(tile_mesh)
                tile_ids.append(tile.tile_id)

                # Create translated copy for combined mesh
                # Each tile is generated at local origin, so we translate it
                # to its correct position in the combined mesh
                offset_mesh = o3d.geometry.TriangleMesh(tile_mesh)
                offset_mesh.translate((tile.mesh_offset_x, tile.mesh_offset_y, 0.0))
                offset_tile_meshes.append(offset_mesh)

                logger.info(
                    f"Tile {tile.tile_id} mesh created with {len(tile_mesh.vertices)} vertices, "
                    f"offset ({tile.mesh_offset_x}, {tile.mesh_offset_y})"
                )
            else:
                logger.warning(f"No mesh generated for tile {tile.tile_id}")

        # Combine all offset tile meshes into a single combined mesh
        combined_mesh = self.mesh_combiner.combine_meshes(offset_tile_meshes)
        logger.info(f"Combined {len(tile_meshes)} tile meshes")

        if combined_mesh is None:
            return None

        return SplitMeshResult(
            combined_mesh=combined_mesh,
            split_meshes=tile_meshes,
            split_planes=[],  # No split planes for heightmap-based splitting
            tile_ids=tile_ids,
            tile_grid=grid_dims,
        )

    def _generate_tile_mesh(
        self, tile_heightmap: HeightmapData, tile_id: str
    ) -> Union[o3d.geometry.TriangleMesh, None]:
        """
        Generate a complete mesh for a single tile.

        Processes all threshold levels and combines them into one mesh.
        Also stores threshold snapshots for this tile in self.tile_snapshots.

        Each tile gets an exterior buffer added around it so the contour
        extraction can find the edges properly.

        Args:
            tile_heightmap: Heightmap data for this tile
            tile_id: Identifier for this tile (e.g., "r0c1")

        Returns:
            Combined mesh for this tile
        """
        all_level_meshes: list[o3d.geometry.TriangleMesh] = []

        # Add exterior buffer to this tile for contour extraction
        # The buffer creates a "ring" of constant values around the data
        # so contour extraction can find the boundary
        buffer_width = self.config.heightmap_processing.exterior_buffer_width
        buffer_value = self.config.heightmap_processing.exterior_buffer_value

        if buffer_width > 0:
            tile_heightmap.data = np.pad(
                tile_heightmap.data,
                pad_width=buffer_width,
                mode="constant",
                constant_values=buffer_value,
            )
            logger.debug(
                f"Tile {tile_id}: Added {buffer_width}px buffer with value {buffer_value}"
            )

        # Initialize snapshot storage for this tile
        if not self.config.stateless:
            self.tile_snapshots[tile_id] = {}

        for level_idx, threshold in enumerate(
            self.config.heightmap_processing.thresholds
        ):
            level_height = self.config.heightmap_processing.base_height + (
                level_idx * self.config.heightmap_processing.layer_thickness
            )

            # Create snapshot for this tile's level
            if not self.config.stateless:
                self.tile_snapshots[tile_id][level_idx] = ThresholdSnapshot(
                    threshold=threshold
                )

            mesh_ls = self._generate_mesh_for_tile(
                tile_heightmap,
                level_idx,
                threshold,
                level_height,
                tile_id,
            )

            if self.config.post_processing.apply_post_processing:
                mesh_ls = [self.mesh_processor.process_mesh(mesh) for mesh in mesh_ls]

            for mesh in mesh_ls:
                if len(mesh.vertices) > 0:
                    all_level_meshes.append(mesh)

        # Combine all level meshes for this tile
        tile_combined = self.mesh_combiner.combine_meshes(all_level_meshes)

        # Final post-processing on combined tile mesh
        if self.config.post_processing.apply_post_processing:
            tile_combined = self.mesh_processor.process_mesh(tile_combined)

        return tile_combined

    def _generate_mesh_for_tile(
        self,
        heightmap_data: HeightmapData,
        level_idx: int,
        threshold: float,
        base_height: float,
        tile_id: str,
    ) -> list[o3d.geometry.TriangleMesh]:
        """
        Generate mesh for a single level of a tile.

        Similar to generate_mesh() but stores snapshots in tile_snapshots instead
        of threshold_snapshots.

        Args:
            heightmap_data: Heightmap data for this tile
            level_idx: Level index
            threshold: Height threshold
            base_height: Base Z-coordinate
            tile_id: Tile identifier for snapshot storage

        Returns:
            List of meshes for this level
        """
        thickness = self.config.heightmap_processing.layer_thickness

        polygons = self.contour_extractor.extract_contour_polygons(
            heightmap_data.data, threshold
        )

        if not polygons:
            logger.debug(f"Tile {tile_id}: No contours found at threshold {threshold}")
            return []

        triangles = [
            self._build_extruded_mesh(polygon, base_height, thickness, level_idx)
            for polygon in polygons
        ]

        # Store contours in tile-specific snapshot
        if not self.config.stateless and tile_id in self.tile_snapshots:
            if level_idx in self.tile_snapshots[tile_id]:
                self.tile_snapshots[tile_id][level_idx].contours = polygons

        return triangles

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

        if not self.config.stateless:
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
            polygon: Polygon to triangulate and extrude
            base_height: Base Z-coordinate
            thickness: Extrusion thickness
            level_idx: Level index for snapshot tracking

        Returns:
            Open3D TriangleMesh object
        """
        # Use triangulate_polygon_with_info to get boundary vertex information
        tri_result = self.triangulator.triangulate_polygon_with_info(polygon)
        vertices_2d = tri_result.vertices
        triangles = tri_result.triangles
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

        # Create side faces using direct boundary indexing (no closest-vertex matching)
        side_faces = self._create_side_faces_from_triangulation(tri_result, n_vertices)

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

        if not self.config.stateless:
            snapshot = self.threshold_snapshots.get(level_idx)
            if snapshot:
                if snapshot.vertices_2d is None:
                    snapshot.vertices_2d = []
                if snapshot.triangles is None:
                    snapshot.triangles = []

                snapshot.vertices_2d.append(vertices_2d)
                snapshot.triangles.append(triangles)

        return mesh

    def _create_side_faces_from_triangulation(
        self, tri_result: TriangulationResult, n_vertices: int
    ) -> np.ndarray:
        """
        Create side faces for extruded mesh using triangulation boundary info.

        Uses direct indexing from TriangulationResult to ensure correct
        vertex references for side faces. Handles both exterior and hole boundaries.

        Args:
            tri_result: Triangulation result with boundary vertex information
            n_vertices: Number of vertices in each layer (bottom/top)

        Returns:
            Array of side face indices
        """
        side_faces = []

        # Create side faces for exterior ring
        exterior_indices = tri_result.get_exterior_indices()
        exterior_side_faces = self._create_ring_side_faces(
            exterior_indices, n_vertices, reverse_winding=False
        )
        side_faces.extend(exterior_side_faces)

        # Create side faces for each hole ring (reversed winding for interior walls)
        for hole_idx in range(len(tri_result.hole_vertex_counts)):
            hole_indices = tri_result.get_hole_indices(hole_idx)
            hole_side_faces = self._create_ring_side_faces(
                hole_indices, n_vertices, reverse_winding=True
            )
            side_faces.extend(hole_side_faces)

        return np.array(side_faces) if side_faces else np.array([])

    def _create_ring_side_faces(
        self,
        boundary_indices: list[int],
        n_vertices: int,
        reverse_winding: bool = False,
    ) -> list[list[int]]:
        """
        Create side faces for a single boundary ring (exterior or hole).

        Args:
            boundary_indices: Vertex indices for this ring
            n_vertices: Number of vertices in each layer
            reverse_winding: If True, reverse face winding (for hole interiors)

        Returns:
            List of triangle face indices
        """
        if len(boundary_indices) < 3:
            logger.warning("Insufficient boundary vertices for side faces")
            return []

        faces = []
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
            if reverse_winding:
                # Reversed winding for hole interior walls (normals face inward)
                faces.extend(
                    [
                        [curr_idx, curr_idx + n_vertices, next_idx + n_vertices],
                        [curr_idx, next_idx + n_vertices, next_idx],
                    ]
                )
            else:
                # Normal winding for exterior walls (normals face outward)
                faces.extend(
                    [
                        [curr_idx, next_idx, next_idx + n_vertices],
                        [curr_idx, next_idx + n_vertices, curr_idx + n_vertices],
                    ]
                )

        return faces

    def _create_side_faces(
        self, vertices_2d: np.ndarray, polygon: Polygon, n_vertices: int
    ) -> np.ndarray:
        """
        Create side faces for extruded mesh from polygon boundary.

        DEPRECATED: Use _create_side_faces_from_triangulation instead.
        This method uses closest-vertex matching which can cause errors
        when interior points are added during triangulation.

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
