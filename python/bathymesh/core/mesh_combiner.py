"""Mesh combination and manipulation utilities."""

from typing import List, Optional
import numpy as np
import open3d as o3d
import logging

logger = logging.getLogger(__name__)


class MeshCombiner:
    """Combines and manipulates multiple meshes."""
    
    merge_threshold: float
    
    def __init__(self, merge_threshold: float = 1e-6):
        """
        Initialize mesh combiner.
        
        Args:
            merge_threshold: Distance threshold for merging close vertices
        """
        self.merge_threshold = merge_threshold
    
    def combine_meshes(self, meshes: List[o3d.geometry.TriangleMesh]) -> o3d.geometry.TriangleMesh:
        """
        Combine multiple meshes into a single mesh.
        
        Args:
            meshes: List of Open3D TriangleMesh objects to combine
            
        Returns:
            Combined Open3D TriangleMesh object
            
        Raises:
            ValueError: If no valid meshes provided
        """
        if not meshes:
            raise ValueError("No meshes provided for combination")
        
        # Filter out empty meshes
        valid_meshes = [mesh for mesh in meshes if len(mesh.vertices) > 0]
        
        if not valid_meshes:
            logger.warning("No valid meshes found, returning empty mesh")
            return o3d.geometry.TriangleMesh()
        
        logger.info(f"Combining {len(valid_meshes)} meshes")
        
        # Start with first mesh
        combined = valid_meshes[0]
        
        # Add remaining meshes
        for i, mesh in enumerate(valid_meshes[1:], 1):
            try:
                combined += mesh
                logger.debug(f"Added mesh {i+1}/{len(valid_meshes)}")
            except Exception as e:
                logger.warning(f"Failed to add mesh {i+1}: {e}")
                continue
        
        # Clean up the combined mesh
        combined = self._clean_mesh(combined)
        
        logger.info(f"Combined mesh has {len(combined.vertices)} vertices and {len(combined.triangles)} triangles")
        return combined
    
    def create_simple_surface_mesh(
        self, 
        vertices: np.ndarray, 
        faces: np.ndarray
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a simple surface mesh from vertices and faces.
        
        Args:
            vertices: (N, 3) array of vertex coordinates
            faces: (M, 3) array of triangle vertex indices
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If vertices or faces have invalid shape
        """
        if vertices.shape[1] != 3:
            raise ValueError(f"Vertices must have shape (N, 3), got {vertices.shape}")
        
        if faces.shape[1] != 3:
            raise ValueError(f"Faces must have shape (M, 3), got {faces.shape}")
        
        # Validate face indices
        max_vertex_idx = len(vertices) - 1
        if faces.max() > max_vertex_idx:
            raise ValueError(f"Face indices exceed vertex count: max {faces.max()} > {max_vertex_idx}")
        
        # Create mesh
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(faces)
        
        # Clean and compute normals
        mesh = self._clean_mesh(mesh)
        
        logger.debug(f"Created surface mesh with {len(vertices)} vertices and {len(faces)} triangles")
        return mesh
    
    def _clean_mesh(self, mesh: o3d.geometry.TriangleMesh) -> o3d.geometry.TriangleMesh:
        """
        Clean mesh by merging close vertices and computing normals.
        
        Args:
            mesh: Open3D TriangleMesh to clean
            
        Returns:
            Cleaned mesh
        """
        if len(mesh.vertices) == 0:
            return mesh
        
        original_vertices = len(mesh.vertices)
        original_triangles = len(mesh.triangles)
        
        # Merge close vertices
        mesh.merge_close_vertices(self.merge_threshold)
        
        # Remove degenerate triangles and unreferenced vertices
        mesh.remove_degenerate_triangles()
        mesh.remove_unreferenced_vertices()
        
        # Compute vertex normals
        mesh.compute_vertex_normals()
        
        final_vertices = len(mesh.vertices)
        final_triangles = len(mesh.triangles)
        
        logger.debug(f"Mesh cleaning: vertices {original_vertices} -> {final_vertices}, "
                    f"triangles {original_triangles} -> {final_triangles}")
        
        return mesh
