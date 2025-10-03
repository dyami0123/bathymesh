"""Polygon to mesh conversion functionality."""

from typing import Union, List
import numpy as np
import open3d as o3d
from shapely.geometry import Polygon
import logging

from ..triangulation import TriangleTriangulator

logger = logging.getLogger(__name__)


class PolygonMeshGenerator:
    """Converts polygons to 3D meshes with optional extrusion."""
    
    triangulator: TriangleTriangulator
    
    def __init__(self, triangulator: Union[TriangleTriangulator, None] = None):
        """
        Initialize polygon mesh generator.
        
        Args:
            triangulator: Triangulation engine. If None, creates default instance.
        """
        self.triangulator = triangulator or TriangleTriangulator(quality_mesh=True)
    
    def create_flat_mesh(
        self, 
        polygon: Polygon, 
        height: float = 0.0
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a flat mesh from a polygon at specified height.
        
        Args:
            polygon: Shapely Polygon to convert
            height: Z-coordinate for the flat mesh
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If polygon triangulation fails
        """
        try:
            vertices_2d, triangles = self.triangulator.triangulate_polygon(polygon)
        except Exception as e:
            raise ValueError(f"Failed to triangulate polygon: {e}") from e
        
        # Create 3D vertices at specified height
        vertices_3d = np.column_stack((vertices_2d, np.full(len(vertices_2d), height)))
        
        # Create Open3D mesh
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices_3d)
        mesh.triangles = o3d.utility.Vector3iVector(triangles)
        mesh.compute_vertex_normals()
        
        logger.debug(f"Created flat mesh with {len(vertices_3d)} vertices and {len(triangles)} triangles")
        return mesh
    
    def create_extruded_mesh(
        self, 
        polygon: Polygon, 
        base_height: float = 0.0, 
        thickness: float = 1.0
    ) -> o3d.geometry.TriangleMesh:
        """
        Create an extruded 3D mesh from a polygon.
        
        Args:
            polygon: Shapely Polygon to extrude
            base_height: Z-coordinate of the base
            thickness: Extrusion thickness
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If polygon triangulation or mesh creation fails
        """
        try:
            vertices_2d, triangles = self.triangulator.triangulate_polygon(polygon)
        except Exception as e:
            raise ValueError(f"Failed to triangulate polygon: {e}") from e
        
        try:
            return self._build_extruded_mesh(vertices_2d, triangles, polygon, base_height, thickness)
        except Exception as e:
            logger.warning(f"Extruded mesh creation failed: {e}, falling back to flat mesh")
            return self.create_flat_mesh(polygon, base_height)
    
    def _build_extruded_mesh(
        self, 
        vertices_2d: np.ndarray, 
        triangles: np.ndarray, 
        polygon: Polygon, 
        base_height: float, 
        thickness: float
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
        n_vertices = len(vertices_2d)
        
        # Create 3D vertices for bottom and top
        bottom_z = base_height
        top_z = base_height + thickness
        bottom_vertices = np.column_stack((vertices_2d, np.full(n_vertices, bottom_z)))
        top_vertices = np.column_stack((vertices_2d, np.full(n_vertices, top_z)))
        
        all_vertices = np.vstack((bottom_vertices, top_vertices))
        
        # Create faces
        bottom_faces = triangles
        top_faces = triangles[:, ::-1] + n_vertices  # Reverse winding and offset indices
        
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
            raise ValueError(f"Invalid face indices: max {faces.max()} > {max_vertex_idx}")
        
        # Create Open3D mesh
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(all_vertices)
        mesh.triangles = o3d.utility.Vector3iVector(faces)
        mesh.compute_vertex_normals()
        
        logger.debug(f"Created extruded mesh with {len(all_vertices)} vertices and {len(faces)} triangles")
        return mesh
    
    def _create_side_faces(
        self, 
        vertices_2d: np.ndarray, 
        polygon: Polygon, 
        n_vertices: int
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
                logger.warning(f"Invalid boundary index {curr_idx} or {next_idx}, skipping")
                continue
            
            # Two triangles for each boundary edge
            side_faces.extend([
                [curr_idx, next_idx, next_idx + n_vertices],
                [curr_idx, next_idx + n_vertices, curr_idx + n_vertices]
            ])
        
        return np.array(side_faces) if side_faces else np.array([])
    
    def _map_boundary_to_vertices(
        self, 
        boundary_coords: np.ndarray, 
        vertices_2d: np.ndarray
    ) -> List[int]:
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
            distances = np.sum((vertices_2d - boundary_point)**2, axis=1)
            closest_idx = np.argmin(distances)
            boundary_indices.append(closest_idx)
        
        return boundary_indices
