"""Polygon to mesh conversion functionality - Legacy facade for new mesh generators."""

from typing import Union, Callable, Optional
import open3d as o3d
from shapely.geometry import Polygon
import logging

from .. import triangulation as tri
from .mesh_generators import BaseMeshGenerator, FlatMeshGenerator, ExtrudedMeshGenerator, HeightmapMeshGenerator
from .heightmap_processor import HeightmapProcessor
from .mesh_combiner import MeshCombiner

logger = logging.getLogger(__name__)


class PolygonMeshGenerator:
    """
    Legacy facade for polygon mesh generation - delegates to specialized generators.
    
    This class maintains backward compatibility while using the new mesh generator architecture.
    For new code, consider using the specific mesh generators directly with HeightmapHandler.
    """

    triangulator: tri.BaseTriangulator
    heightmap_processor: HeightmapProcessor
    mesh_combiner: MeshCombiner
    flat_generator: BaseMeshGenerator
    extruded_generator: BaseMeshGenerator
    heightmap_generator: BaseMeshGenerator
    
    def __init__(
        self, 
        triangulator: Optional[tri.BaseTriangulator] = None,
        heightmap_processor: Optional[HeightmapProcessor] = None,
        mesh_combiner: Optional[MeshCombiner] = None
    ):
        """
        Initialize polygon mesh generator facade.
        
        Args:
            triangulator: Triangulation engine. If None, creates default instance.
            heightmap_processor: Heightmap processor. If None, creates default instance.
            mesh_combiner: Mesh combiner. If None, creates default instance.
        """
        # self.triangulator = triangulator or GmshTriangulator(quality_mesh=True)
        self.triangulator = triangulator or tri.ScipyTriangulator(quality_mesh=True)
        self.heightmap_processor = heightmap_processor or HeightmapProcessor()
        self.mesh_combiner = mesh_combiner or MeshCombiner()
        
        # Initialize specialized generators
        self.flat_generator = FlatMeshGenerator(
            self.triangulator, 
            self.heightmap_processor, 
            self.mesh_combiner
        )
        self.extruded_generator = ExtrudedMeshGenerator(
            self.triangulator, 
            self.heightmap_processor, 
            self.mesh_combiner
        )
        self.heightmap_generator = HeightmapMeshGenerator(
            self.triangulator, 
            self.heightmap_processor, 
            self.mesh_combiner
        )
    
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
        return self.flat_generator.generate_mesh_from_polygons(polygon, height=height)
    
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
        return self.extruded_generator.generate_mesh_from_polygons(
            polygon, 
            base_height=base_height, 
            thickness=thickness
        )
    
    def create_heightmap_mesh(
        self,
        polygon: Polygon,
        height_function: Callable[[float, float], float],
        base_height: float = 0.0
    ) -> o3d.geometry.TriangleMesh:
        """
        Create a mesh with height variations from a polygon.
        
        Args:
            polygon: Shapely Polygon to convert
            height_function: Function that takes (x, y) coordinates and returns height
            base_height: Base Z-coordinate to add to height function results
            
        Returns:
            Open3D TriangleMesh object
            
        Raises:
            ValueError: If polygon triangulation fails
        """
        return self.heightmap_generator.generate_mesh_from_function(
            polygon,
            height_function=height_function,
            base_height=base_height
        )
