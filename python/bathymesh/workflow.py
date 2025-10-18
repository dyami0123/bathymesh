"""Main workflow class for bathymesh operations."""

from typing import List, Optional, Union, Literal
from pathlib import Path
import numpy as np
import open3d as o3d
import logging

from .core import (
    HeightmapProcessor, 
    HeightmapHandler,
    PolygonMeshGenerator, 
    MeshCombiner,
    BaseMeshGenerator,
    FlatMeshGenerator,
    ExtrudedMeshGenerator,
    HeightmapMeshGenerator
)
from . import triangulation
from .io import export_mesh, get_mesh_info
from .utils import validate_heightmap, create_test_heightmap
from .data_structures import MeshInfo, MeshScaling, MeshType

logger = logging.getLogger(__name__)


class BathymeshWorkflow:
    """Main workflow class that orchestrates bathymesh operations."""
    
    heightmap_processor: HeightmapProcessor
    triangulator: triangulation.BaseTriangulator
    polygon_generator: PolygonMeshGenerator
    mesh_combiner: MeshCombiner
    flat_generator: BaseMeshGenerator
    extruded_generator: BaseMeshGenerator
    heightmap_generator: BaseMeshGenerator
    
    def __init__(
        self,
        min_polygon_area: float = 1e-2,
        merge_threshold: float = 1e-6,
        quality_triangulation: bool = True,
        triangulator: Optional[triangulation.BaseTriangulator] = None
    ):
        """
        Initialize bathymesh workflow.
        
        Args:
            min_polygon_area: Minimum area threshold for valid polygons
            merge_threshold: Distance threshold for merging close vertices
            quality_triangulation: Use quality triangulation (Delaunay)
            triangulator: Optional custom triangulator implementation
        """
        self.heightmap_processor = HeightmapProcessor(min_polygon_area=min_polygon_area)
        self.triangulator = triangulator or triangulation.ScipyTriangulator()
        self.mesh_combiner = MeshCombiner(merge_threshold=merge_threshold)
        
        # Legacy polygon generator for backward compatibility
        self.polygon_generator = PolygonMeshGenerator(
            triangulator=self.triangulator,
            heightmap_processor=self.heightmap_processor,
            mesh_combiner=self.mesh_combiner
        )
        
        # New specialized generators
        self.flat_generator = FlatMeshGenerator(
            self.triangulator, self.heightmap_processor, self.mesh_combiner
        )
        self.extruded_generator = ExtrudedMeshGenerator(
            self.triangulator, self.heightmap_processor, self.mesh_combiner
        )
        self.heightmap_generator = HeightmapMeshGenerator(
            self.triangulator, self.heightmap_processor, self.mesh_combiner
        )
    
    def create_mesh_from_heightmap(
        self,
        heightmap: np.ndarray,
        mesh_type: Union[MeshType, str] = MeshType.SURFACE,
        scaling: Optional[MeshScaling] = None,
        x_coords: Optional[np.ndarray] = None,
        y_coords: Optional[np.ndarray] = None,
        base_height: float = 0.0,
        thickness: float = 1.0,
        flat_height: Optional[float] = None,
        use_contours: bool = False,
        contour_threshold: Optional[float] = None,
        output_path: Optional[Union[str, Path]] = None
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a mesh from heightmap data using the specified generation strategy.
        
        Args:
            heightmap: 2D numpy array of height values
            mesh_type: Type of mesh to generate (flat, extruded, surface, contour)
            scaling: MeshScaling for coordinate transformation
            x_coords: Optional x-coordinates array
            y_coords: Optional y-coordinates array
            base_height: Base Z-coordinate for mesh
            thickness: Thickness for extruded meshes
            flat_height: Height for flat meshes (uses base_height if None)
            use_contours: Whether to extract contours for polygon-based generation
            contour_threshold: Threshold for contour extraction
            output_path: Optional path to save the mesh
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If parameters are invalid
        """
        logger.info(f"Creating {mesh_type} mesh from heightmap with shape {heightmap.shape}")
        validate_heightmap(heightmap)
        
        # Normalize mesh_type
        if isinstance(mesh_type, str):
            try:
                mesh_type = MeshType(mesh_type.lower())
            except ValueError:
                raise ValueError(f"Invalid mesh_type '{mesh_type}'. Valid options: {[t.value for t in MeshType]}")
        
        # Create heightmap handler
        heightmap_handler = HeightmapHandler(
            heightmap=heightmap,
            x_coords=x_coords,
            y_coords=y_coords,
            scaling=scaling or MeshScaling(),
            processor=self.heightmap_processor
        )
        
        # Generate mesh based on type
        if mesh_type == MeshType.FLAT:
            height = flat_height if flat_height is not None else base_height
            mesh = self.flat_generator.generate_mesh(
                heightmap_handler,
                height=height,
                use_contours=use_contours,
                threshold=contour_threshold
            )
        
        elif mesh_type == MeshType.EXTRUDED:
            mesh = self.extruded_generator.generate_mesh(
                heightmap_handler,
                base_height=base_height,
                thickness=thickness,
                use_contours=use_contours,
                threshold=contour_threshold
            )
        
        elif mesh_type == MeshType.SURFACE:
            mesh = self.heightmap_generator.generate_mesh(
                heightmap_handler,
                base_height=base_height,
                use_surface_mesh=True
            )
        
        elif mesh_type == MeshType.CONTOUR:
            if contour_threshold is None:
                # Use mid-range threshold if none provided
                min_height, max_height = heightmap_handler.height_range
                contour_threshold = (min_height + max_height) / 2
                logger.info(f"Using automatic contour threshold: {contour_threshold:.3f}")
            
            mesh = self.heightmap_generator.generate_mesh(
                heightmap_handler,
                base_height=base_height,
                use_contours=True,
                threshold=contour_threshold
            )
        
        else:
            raise ValueError(f"Unsupported mesh_type: {mesh_type}")
        
        # Export if path provided
        if output_path:
            export_mesh(mesh, output_path)
            logger.info(f"Mesh exported to {output_path}")
        
        logger.info(f"{mesh_type.value.title()} mesh created with {len(mesh.vertices)} vertices")
        return mesh
    
    def create_multi_level_mesh(
        self,
        heightmap: np.ndarray,
        thresholds: List[float],
        mesh_type: Union[MeshType, str] = MeshType.EXTRUDED,
        scaling: Optional[MeshScaling] = None,
        x_coords: Optional[np.ndarray] = None,
        y_coords: Optional[np.ndarray] = None,
        base_height: float = 0.0,
        thickness: float = 1.0,
        layer_spacing: Optional[float] = None,
        output_path: Optional[Union[str, Path]] = None
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a multi-level mesh from heightmap data at multiple thresholds.
        
        Args:
            heightmap: 2D numpy array of height values
            thresholds: List of height thresholds for contour extraction
            mesh_type: Type of mesh to generate for each level
            scaling: MeshScaling for coordinate transformation
            x_coords: Optional x-coordinates array
            y_coords: Optional y-coordinates array
            base_height: Base Z-coordinate for the first level
            thickness: Thickness for extruded meshes
            layer_spacing: Vertical spacing between levels (uses thickness if None)
            output_path: Optional path to save the combined mesh
            
        Returns:
            Combined Open3D TriangleMesh object
        """
        logger.info(f"Creating multi-level {mesh_type} mesh with {len(thresholds)} levels")
        validate_heightmap(heightmap)
        
        if not thresholds:
            raise ValueError("At least one threshold must be provided")
        
        # Normalize mesh_type
        if isinstance(mesh_type, str):
            try:
                mesh_type = MeshType(mesh_type.lower())
            except ValueError:
                raise ValueError(f"Invalid mesh_type '{mesh_type}'. Valid options: {[t.value for t in MeshType]}")
        
        if mesh_type == MeshType.SURFACE:
            logger.warning("Surface mesh type not suitable for multi-level generation, using extruded instead")
            mesh_type = MeshType.EXTRUDED
        
        # Create heightmap handler
        heightmap_handler = HeightmapHandler(
            heightmap=heightmap,
            x_coords=x_coords,
            y_coords=y_coords,
            scaling=scaling or MeshScaling(),
            processor=self.heightmap_processor
        )
        
        layer_offset = layer_spacing or thickness
        all_meshes = []
        
        for level_idx, threshold in enumerate(thresholds):
            level_height = base_height + (level_idx * layer_offset)
            logger.debug(f"Processing level {level_idx + 1}/{len(thresholds)} at threshold {threshold}, height {level_height}")
            
            try:
                if mesh_type == MeshType.FLAT:
                    mesh = self.flat_generator.generate_mesh(
                        heightmap_handler,
                        height=level_height,
                        use_contours=True,
                        threshold=threshold
                    )
                
                elif mesh_type == MeshType.EXTRUDED:
                    mesh = self.extruded_generator.generate_mesh(
                        heightmap_handler,
                        base_height=level_height,
                        thickness=thickness,
                        use_contours=True,
                        threshold=threshold
                    )
                
                elif mesh_type == MeshType.CONTOUR:
                    mesh = self.heightmap_generator.generate_mesh(
                        heightmap_handler,
                        base_height=level_height,
                        use_contours=True,
                        threshold=threshold
                    )
                
                if len(mesh.vertices) > 0:
                    all_meshes.append(mesh)
                    logger.debug(f"Level {level_idx + 1} mesh created with {len(mesh.vertices)} vertices")
                else:
                    logger.warning(f"No mesh generated for level {level_idx + 1} at threshold {threshold}")
                    
            except Exception as e:
                logger.warning(f"Failed to create mesh for level {level_idx + 1} at threshold {threshold}: {e}")
                continue
        
        if not all_meshes:
            logger.warning("No valid meshes created, returning empty mesh")
            return o3d.geometry.TriangleMesh()
        
        # Combine all level meshes
        combined_mesh = self.mesh_combiner.combine_meshes(all_meshes)
        
        # Export if path provided
        if output_path:
            export_mesh(combined_mesh, output_path)
            logger.info(f"Multi-level mesh exported to {output_path}")
        
        logger.info(f"Multi-level mesh created with {len(combined_mesh.vertices)} vertices from {len(all_meshes)} levels")
        return combined_mesh
    
    # Legacy methods for backward compatibility
    def create_simple_surface_mesh(
        self,
        heightmap: np.ndarray,
        scaling: MeshScaling = MeshScaling(),
        output_path: Optional[Union[str, Path]] = None
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a simple surface mesh directly from heightmap (legacy method).
        
        Args:
            heightmap: 2D numpy array of height values
            scaling: MeshScaling dataclass with scaling factors for each dimension
            output_path: Optional path to save the mesh
            
        Returns:
            Open3D TriangleMesh object
        """
        logger.info("Creating simple surface mesh from heightmap (legacy method)")
        return self.create_mesh_from_heightmap(
            heightmap=heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=scaling,
            output_path=output_path
        )
    
    def create_contour_mesh(
        self,
        heightmap: np.ndarray,
        thresholds: List[float],
        thickness: float = 1.0,
        extrude: bool = True,
        output_path: Optional[Union[str, Path]] = None
    ) -> o3d.geometry.TriangleMesh:
        """
        Create mesh from heightmap contours at specified thresholds (legacy method).
        
        Args:
            heightmap: 2D numpy array of height values
            thresholds: List of height values to extract contours at
            thickness: Thickness for extrusion (or layer spacing if not extruding)
            extrude: If True, creates extruded meshes; if False, creates flat polygons
            output_path: Optional path to save the mesh
            
        Returns:
            Combined Open3D TriangleMesh object
        """
        logger.info(f"Creating contour mesh with {len(thresholds)} thresholds, extrude={extrude} (legacy method)")
        
        mesh_type = MeshType.EXTRUDED if extrude else MeshType.FLAT
        return self.create_multi_level_mesh(
            heightmap=heightmap,
            thresholds=thresholds,
            mesh_type=mesh_type,
            thickness=thickness,
            layer_spacing=thickness,
            output_path=output_path
        )
    
    def get_mesh_info(self, mesh: o3d.geometry.TriangleMesh) -> MeshInfo:
        """
        Get detailed information about a mesh.
        
        Args:
            mesh: Open3D TriangleMesh to analyze
            
        Returns:
            MeshInfo dataclass with mesh information
        """
        return get_mesh_info(mesh)
    
    def get_supported_mesh_types(self) -> List[str]:
        """
        Get list of supported mesh types.
        
        Returns:
            List of supported mesh type strings
        """
        return [mesh_type.value for mesh_type in MeshType]
    
    def create_heightmap_handler(
        self,
        heightmap: np.ndarray,
        scaling: Optional[MeshScaling] = None,
        x_coords: Optional[np.ndarray] = None,
        y_coords: Optional[np.ndarray] = None
    ) -> HeightmapHandler:
        """
        Create a HeightmapHandler instance with the workflow's processors.
        
        Args:
            heightmap: 2D numpy array of height values
            scaling: Optional MeshScaling for coordinate transformation
            x_coords: Optional x-coordinates array
            y_coords: Optional y-coordinates array
            
        Returns:
            Configured HeightmapHandler instance
        """
        return HeightmapHandler(
            heightmap=heightmap,
            x_coords=x_coords,
            y_coords=y_coords,
            scaling=scaling or MeshScaling(),
            processor=self.heightmap_processor
        )
