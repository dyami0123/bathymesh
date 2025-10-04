"""Extruded mesh generation implementation."""

from typing import Union, List, Optional, TYPE_CHECKING
import numpy as np
import open3d as o3d
from shapely.geometry import Polygon, MultiPolygon
import logging

from .base_mesh_generator import BaseMeshGenerator

if TYPE_CHECKING:
    from ..heightmap_handler import HeightmapHandler

logger = logging.getLogger(__name__)


class ExtrudedMeshGenerator(BaseMeshGenerator):
    """Generates extruded 3D meshes from heightmap data."""
    
    def generate_mesh(
        self, 
        heightmap_handler: 'HeightmapHandler',
        base_height: float = 0.0,
        thickness: float = 1.0,
        use_contours: bool = False,
        threshold: Optional[float] = None
    ) -> o3d.geometry.TriangleMesh:
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
        if use_contours:
            if threshold is None:
                raise ValueError("threshold must be provided when use_contours=True")
            polygons = heightmap_handler.extract_contour_polygons(threshold)
            if not polygons:
                logger.warning("No contours found at threshold, using bounding polygon")
                polygon = heightmap_handler.get_bounding_polygon()
            else:
                # For now, use the first/largest polygon
                polygon = max(polygons, key=lambda p: p.area)
        else:
            polygon = heightmap_handler.get_bounding_polygon()
        
        return self._create_extruded_mesh_single(polygon, base_height, thickness)
    
    def generate_mesh_from_polygons(
        self,
        geometries: Union[Polygon, MultiPolygon, List[Polygon]],
        base_height: float = 0.0,
        thickness: float = 1.0
    ) -> o3d.geometry.TriangleMesh:
        """
        Generate an extruded 3D mesh from explicit polygon geometries (legacy interface).
        
        Args:
            geometries: Single polygon, MultiPolygon, or list of polygons
            base_height: Z-coordinate of the base
            thickness: Extrusion thickness
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If polygon triangulation or mesh creation fails
        """
        polygons = self._normalize_geometries(geometries)
        
        # For now, handle single polygon - future enhancement for multiple polygons
        if len(polygons) != 1:
            raise ValueError("Multiple polygon mesh generation not yet implemented")
            
        polygon = polygons[0]
        return self._create_extruded_mesh_single(polygon, base_height, thickness)
    
    def _create_extruded_mesh_single(
        self, 
        polygon: Polygon, 
        base_height: float, 
        thickness: float
    ) -> o3d.geometry.TriangleMesh:
        """
        Create an extruded 3D mesh from a single polygon.
        
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
            # Fallback to flat mesh
            from .flat_mesh_generator import FlatMeshGenerator
            flat_generator = FlatMeshGenerator(self.triangulator)
            return flat_generator.generate_mesh(polygon, height=base_height)
    
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
        
        mesh = self._create_mesh_from_vertices_faces(all_vertices, faces)
        
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
