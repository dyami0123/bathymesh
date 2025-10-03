"""Main workflow class for bathymesh operations."""

from typing import List, Optional, Union
from pathlib import Path
import numpy as np
import open3d as o3d
import logging

from .core import HeightmapProcessor, PolygonMeshGenerator, MeshCombiner
from .triangulation import TriangleTriangulator
from .io import export_mesh, get_mesh_info
from .utils import validate_heightmap, create_test_heightmap
from .data_structures import MeshInfo, MeshScaling, ContourMeshParams

logger = logging.getLogger(__name__)


class BathymeshWorkflow:
    """Main workflow class that orchestrates bathymesh operations."""
    
    heightmap_processor: HeightmapProcessor
    triangulator: TriangleTriangulator
    polygon_generator: PolygonMeshGenerator
    mesh_combiner: MeshCombiner
    
    def __init__(
        self,
        min_polygon_area: float = 1e-2,
        merge_threshold: float = 1e-6,
        quality_triangulation: bool = True
    ):
        """
        Initialize bathymesh workflow.
        
        Args:
            min_polygon_area: Minimum area threshold for valid polygons
            merge_threshold: Distance threshold for merging close vertices
            quality_triangulation: Use quality triangulation (Delaunay)
        """
        self.heightmap_processor = HeightmapProcessor(min_polygon_area=min_polygon_area)
        self.triangulator = TriangleTriangulator(quality_mesh=quality_triangulation)
        self.polygon_generator = PolygonMeshGenerator(triangulator=self.triangulator)
        self.mesh_combiner = MeshCombiner(merge_threshold=merge_threshold)
    
    def create_simple_surface_mesh(
        self,
        heightmap: np.ndarray,
        scaling: MeshScaling = MeshScaling(),
        output_path: Union[Union[str, Path], None] = None
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a simple surface mesh directly from heightmap.
        
        Args:
            heightmap: 2D numpy array of height values
            scaling: MeshScaling dataclass with scaling factors for each dimension
            output_path: Optional path to save the mesh
            
        Returns:
            Open3D TriangleMesh object
        """
        logger.info("Creating simple surface mesh from heightmap")
        validate_heightmap(heightmap)
        
        # Generate mesh data
        vertices, faces = self.heightmap_processor.create_simple_surface_mesh_data(
            heightmap, scaling
        )
        
        # Create mesh
        mesh = self.mesh_combiner.create_simple_surface_mesh(vertices, faces)
        
        # Export if path provided
        if output_path:
            export_mesh(mesh, output_path)
        
        logger.info(f"Simple surface mesh created with {len(mesh.vertices)} vertices")
        return mesh
    
    def create_contour_mesh(
        self,
        heightmap: np.ndarray,
        thresholds: List[float],
        thickness: float = 1.0,
        extrude: bool = True,
        output_path: Union[Union[str, Path], None] = None
    ) -> o3d.geometry.TriangleMesh:
        """
        Create mesh from heightmap contours at specified thresholds.
        
        Args:
            heightmap: 2D numpy array of height values
            thresholds: List of height values to extract contours at
            thickness: Thickness for extrusion (or layer spacing if not extruding)
            extrude: If True, creates extruded meshes; if False, creates flat polygons
            output_path: Optional path to save the mesh
            
        Returns:
            Combined Open3D TriangleMesh object
        """
        logger.info(f"Creating contour mesh with {len(thresholds)} thresholds, extrude={extrude}")
        validate_heightmap(heightmap)
        
        if not thresholds:
            raise ValueError("At least one threshold must be provided")
        
        all_meshes = []
        
        for level_idx, threshold in enumerate(thresholds):
            logger.debug(f"Processing threshold {level_idx + 1}/{len(thresholds)}: {threshold}")
            
            # Extract polygons at this threshold
            polygons = self.heightmap_processor.extract_contour_polygons(heightmap, threshold)
            
            if not polygons:
                logger.warning(f"No polygons found at threshold {threshold}")
                continue
            
            # Convert polygons to meshes
            for poly_idx, polygon in enumerate(polygons):
                try:
                    if extrude:
                        mesh = self.polygon_generator.create_extruded_mesh(
                            polygon, 
                            base_height=threshold * thickness, 
                            thickness=thickness
                        )
                    else:
                        mesh = self.polygon_generator.create_flat_mesh(
                            polygon, 
                            height=threshold * thickness
                        )
                    
                    if len(mesh.vertices) > 0:
                        all_meshes.append(mesh)
                        logger.debug(f"Created mesh for polygon {poly_idx} with {len(mesh.vertices)} vertices")
                    
                except Exception as e:
                    logger.warning(f"Failed to create mesh for polygon {poly_idx} at threshold {threshold}: {e}")
                    continue
        
        if not all_meshes:
            logger.warning("No valid meshes created, returning empty mesh")
            return o3d.geometry.TriangleMesh()
        
        # Combine all meshes
        combined_mesh = self.mesh_combiner.combine_meshes(all_meshes)
        
        # Export if path provided
        if output_path:
            export_mesh(combined_mesh, output_path)
        
        logger.info(f"Contour mesh created with {len(combined_mesh.vertices)} vertices")
        return combined_mesh
    
    def get_mesh_info(self, mesh: o3d.geometry.TriangleMesh) -> MeshInfo:
        """
        Get detailed information about a mesh.
        
        Args:
            mesh: Open3D TriangleMesh to analyze
            
        Returns:
            MeshInfo dataclass with mesh information
        """
        return get_mesh_info(mesh)
