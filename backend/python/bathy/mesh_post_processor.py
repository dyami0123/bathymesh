"""Mesh processing operations for cleanup and simplification."""

import logging
from dataclasses import dataclass
from enum import Enum

import open3d as o3d
from bathy.config import MeshGenerationConfig

logger = logging.getLogger(__name__)


@dataclass
class MeshPostProcessor:
    """
    Handles mesh cleanup, validation, and simplification operations.

    Provides tools to clean up generated meshes by removing degenerate geometry,
    duplicate elements, and optionally simplifying the mesh while preserving
    sharp edges and overall shape.
    """

    # Basic cleanup
    remove_degenerate_triangles: bool = True
    remove_duplicated_vertices: bool = True
    remove_duplicated_triangles: bool = True
    remove_unreferenced_vertices: bool = True

    # Vertex merging
    merge_close_vertices: bool = False
    merge_vertices_threshold: float = 1e-6

    # Simplification
    # simplification_method: SimplificationMethod = SimplificationMethod.NONE
    target_triangle_count: int = 100000  # For quadric decimation
    voxel_size: float = 0.05  # For vertex clustering

    @classmethod
    def from_config(cls, config: MeshGenerationConfig) -> "MeshPostProcessor":
        """Create MeshPostProcessor from configuration."""
        return MeshPostProcessor(
            remove_degenerate_triangles=config.post_processing.remove_degenerate_triangles,
            remove_duplicated_vertices=config.post_processing.remove_duplicated_vertices,
            remove_duplicated_triangles=config.post_processing.remove_duplicated_triangles,
            remove_unreferenced_vertices=config.post_processing.remove_unreferenced_vertices,
            merge_close_vertices=config.post_processing.merge_close_vertices,
            merge_vertices_threshold=config.post_processing.merge_vertices_threshold,
            # simplification_method=SimplificationMethod(config.post_processing.simplification_method),
            target_triangle_count=config.post_processing.target_triangle_count,
            voxel_size=config.post_processing.voxel_size,
        )

    def process_mesh(
        self, mesh: o3d.geometry.TriangleMesh
    ) -> o3d.geometry.TriangleMesh:
        """
        Apply all configured processing operations to a mesh.

        Args:
            mesh: Input mesh to process

        Returns:
            Processed mesh (operates in-place but returns for convenience)
        """
        if len(mesh.vertices) == 0:
            logger.warning("Empty mesh provided, skipping processing")
            return mesh

        initial_vertices = len(mesh.vertices)
        initial_triangles = len(mesh.triangles)

        logger.debug(
            f"Processing mesh: {initial_vertices:,} vertices, {initial_triangles:,} triangles"
        )

        # Basic cleanup operations
        mesh = self._cleanup_mesh(mesh)

        # Simplification
        # mesh = self._simplify_mesh(mesh)

        # Final stats
        final_vertices = len(mesh.vertices)
        final_triangles = len(mesh.triangles)

        vertices_removed = initial_vertices - final_vertices
        triangles_removed = initial_triangles - final_triangles
        logger.debug(
            f"Processing complete: {final_vertices:,} vertices (-{vertices_removed:,}), "
            f"{final_triangles:,} triangles (-{triangles_removed:,})"
        )

        return mesh

    def _cleanup_mesh(
        self, mesh: o3d.geometry.TriangleMesh
    ) -> o3d.geometry.TriangleMesh:
        """Apply basic cleanup operations to mesh."""

        if self.remove_degenerate_triangles:
            mesh.remove_degenerate_triangles()
            logger.debug("Removed degenerate triangles")

        if self.remove_duplicated_vertices:
            mesh.remove_duplicated_vertices()
            logger.debug("Removed duplicated vertices")

        if self.remove_duplicated_triangles:
            mesh.remove_duplicated_triangles()
            logger.debug("Removed duplicated triangles")

        if self.remove_unreferenced_vertices:
            mesh.remove_unreferenced_vertices()
            logger.debug("Removed unreferenced vertices")

        if self.merge_close_vertices:
            mesh.merge_close_vertices(self.merge_vertices_threshold)
            logger.debug(
                f"Merged vertices within {self.merge_vertices_threshold} threshold"
            )

        return mesh

    # def _simplify_mesh(
    #     self, mesh: o3d.geometry.TriangleMesh
    # ) -> o3d.geometry.TriangleMesh:
    #     """Apply simplification to mesh based on configured method."""

    #     if self.simplification_method == SimplificationMethod.NONE:
    #         return mesh

    #     initial_triangles = len(mesh.triangles)

    #     if self.simplification_method == SimplificationMethod.VERTEX_CLUSTERING:
    #         mesh = mesh.simplify_vertex_clustering(
    #             voxel_size=self.voxel_size,
    #             contraction=o3d.geometry.SimplificationContraction.Average,
    #         )
    #         final_triangles = len(mesh.triangles)
    #         logger.debug(
    #             f"Vertex clustering simplification: {initial_triangles:,} → "
    #             f"{final_triangles:,} triangles (voxel_size={self.voxel_size})"
    #         )

    #     elif self.simplification_method == SimplificationMethod.QUADRIC_DECIMATION:
    #         mesh = mesh.simplify_quadric_decimation(
    #             target_number_of_triangles=self.target_triangle_count
    #         )
    #         final_triangles = len(mesh.triangles)
    #         logger.debug(
    #             f"Quadric decimation simplification: {initial_triangles:,} → "
    #             f"{final_triangles:,} triangles (target={self.target_triangle_count:,})"
    #         )

    #     return mesh

    @staticmethod
    def quick_cleanup(
        mesh: o3d.geometry.TriangleMesh, merge_threshold: float = 1e-6
    ) -> o3d.geometry.TriangleMesh:
        """
        Quick cleanup with default settings.

        Args:
            mesh: Mesh to clean
            merge_threshold: Threshold for merging close vertices

        Returns:
            Cleaned mesh
        """
        processor = MeshPostProcessor(
            merge_close_vertices=True,
            merge_vertices_threshold=merge_threshold,
        )

        return processor.process_mesh(mesh)

    # @staticmethod
    # def simplify(
    #     mesh: o3d.geometry.TriangleMesh,
    #     method: SimplificationMethod = SimplificationMethod.QUADRIC_DECIMATION,
    #     target_triangles: int = 100000,
    #     voxel_size: float = 0.05,
    # ) -> o3d.geometry.TriangleMesh:
    #     """
    #     Simplify mesh with specified method.

    #     Args:
    #         mesh: Mesh to simplify
    #         method: Simplification method to use
    #         target_triangles: Target triangle count (for quadric decimation)
    #         voxel_size: Voxel size (for vertex clustering)

    #     Returns:
    #         Simplified mesh
    #     """
    #     processor = MeshPostProcessor(
    #         simplification_method=method,
    #         target_triangle_count=target_triangles,
    #         voxel_size=voxel_size,
    #     )
    #     return processor.process_mesh(mesh)
