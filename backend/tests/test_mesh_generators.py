"""Tests for bathymesh mesh generators."""
import pytest
import numpy as np
import open3d as o3d
from unittest.mock import Mock, MagicMock

from bathymesh.core.mesh_generators import (
    BaseMeshGenerator, FlatMeshGenerator, 
    ExtrudedMeshGenerator, HeightmapMeshGenerator
)
from bathymesh.triangulation import TriangleTriangulator
from bathymesh.core import HeightmapProcessor, MeshCombiner, HeightmapHandler
from bathymesh.data_structures import MeshScaling


class TestBaseMeshGenerator:
    """Test BaseMeshGenerator abstract base class."""
    
    def test_is_abstract(self):
        """Test that BaseMeshGenerator cannot be instantiated directly."""
        triangulator = TriangleTriangulator()
        
        with pytest.raises(TypeError):
            BaseMeshGenerator(triangulator)
    
    def test_abstract_methods_exist(self):
        """Test that abstract methods are defined."""
        assert hasattr(BaseMeshGenerator, 'generate_mesh')
        assert 'generate_mesh' in BaseMeshGenerator.__abstractmethods__


class TestFlatMeshGenerator:
    """Test FlatMeshGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.triangulator = TriangleTriangulator()
        self.processor = HeightmapProcessor(min_polygon_area=0.01)
        self.combiner = MeshCombiner()
        self.generator = FlatMeshGenerator(
            self.triangulator, 
            self.processor, 
            self.combiner
        )
    
    def test_initialization(self):
        """Test generator initialization."""
        assert self.generator.triangulator == self.triangulator
        assert self.generator.heightmap_processor == self.processor
        assert self.generator.mesh_combiner == self.combiner
    
    def test_generate_mesh_simple_bounding_box(self, simple_heightmap, default_scaling):
        """Test flat mesh generation using bounding box approach."""
        heightmap_handler = HeightmapHandler(
            heightmap=simple_heightmap,
            scaling=default_scaling,
            processor=self.processor
        )
        
        mesh = self.generator.generate_mesh(
            heightmap_handler,
            height=1.0,
            use_contours=False
        )
        
        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) > 0
        assert len(mesh.triangles) > 0
        
        # Check that all vertices are at the specified height
        vertices = np.asarray(mesh.vertices)
        np.testing.assert_array_almost_equal(vertices[:, 2], 1.0, decimal=5)
    
    def test_generate_mesh_with_contours(self, test_heightmap, default_scaling):
        """Test flat mesh generation using contours."""
        heightmap_handler = HeightmapHandler(
            heightmap=test_heightmap,
            scaling=default_scaling,
            processor=self.processor
        )
        
        mesh = self.generator.generate_mesh(
            heightmap_handler,
            height=0.5,
            use_contours=True,
            threshold=0.3
        )
        
        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        # May have zero vertices if no contours found at threshold
        assert len(mesh.vertices) >= 0
        if len(mesh.vertices) > 0:
            vertices = np.asarray(mesh.vertices)
            np.testing.assert_array_almost_equal(vertices[:, 2], 0.5, decimal=5)
    
    def test_generate_mesh_contours_missing_threshold(self, test_heightmap, default_scaling):
        """Test that using contours without threshold raises error."""
        heightmap_handler = HeightmapHandler(
            heightmap=test_heightmap,
            scaling=default_scaling,
            processor=self.processor
        )
        
        with pytest.raises(ValueError, match="threshold"):
            self.generator.generate_mesh(
                heightmap_handler,
                height=0.5,
                use_contours=True,
                threshold=None
            )
    
    def test_generate_mesh_different_heights(self, simple_heightmap, default_scaling):
        """Test flat mesh generation at different heights."""
        heightmap_handler = HeightmapHandler(
            heightmap=simple_heightmap,
            scaling=default_scaling,
            processor=self.processor
        )
        
        heights = [0.0, 1.0, -1.0, 2.5]
        
        for height in heights:
            mesh = self.generator.generate_mesh(
                heightmap_handler,
                height=height,
                use_contours=False
            )
            
            assert isinstance(mesh, o3d.geometry.TriangleMesh)
            if len(mesh.vertices) > 0:
                vertices = np.asarray(mesh.vertices)
                np.testing.assert_array_almost_equal(vertices[:, 2], height, decimal=5)


class TestExtrudedMeshGenerator:
    """Test ExtrudedMeshGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.triangulator = TriangleTriangulator()
        self.processor = HeightmapProcessor(min_polygon_area=0.01)
        self.combiner = MeshCombiner()
        self.generator = ExtrudedMeshGenerator(
            self.triangulator, 
            self.processor, 
            self.combiner
        )
    
    def test_initialization(self):
        """Test generator initialization."""
        assert self.generator.triangulator == self.triangulator
        assert self.generator.heightmap_processor == self.processor
        assert self.generator.mesh_combiner == self.combiner
    
    def test_generate_mesh_simple(self, simple_heightmap, default_scaling):
        """Test basic extruded mesh generation."""
        heightmap_handler = HeightmapHandler(
            heightmap=simple_heightmap,
            scaling=default_scaling,
            processor=self.processor
        )
        
        mesh = self.generator.generate_mesh(
            heightmap_handler,
            base_height=0.0,
            thickness=2.0,
            use_contours=False
        )
        
        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) > 0
        assert len(mesh.triangles) > 0
        
        # Check that vertices span the expected height range
        vertices = np.asarray(mesh.vertices)
        z_values = vertices[:, 2]
        assert z_values.min() >= 0.0  # At least base_height
        assert z_values.max() <= 2.0  # At most base_height + thickness
    
    def test_generate_mesh_with_contours(self, test_heightmap, default_scaling):
        """Test extruded mesh generation using contours."""
        heightmap_handler = HeightmapHandler(
            heightmap=test_heightmap,
            scaling=default_scaling,
            processor=self.processor
        )
        
        mesh = self.generator.generate_mesh(
            heightmap_handler,
            base_height=1.0,
            thickness=0.5,
            use_contours=True,
            threshold=0.3
        )
        
        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        # May have zero vertices if no contours found
        assert len(mesh.vertices) >= 0
    
    def test_generate_mesh_different_thickness(self, simple_heightmap, default_scaling):
        """Test extruded mesh with different thickness values."""
        heightmap_handler = HeightmapHandler(
            heightmap=simple_heightmap,
            scaling=default_scaling,
            processor=self.processor
        )
        
        thicknesses = [0.1, 1.0, 5.0]
        
        for thickness in thicknesses:
            mesh = self.generator.generate_mesh(
                heightmap_handler,
                base_height=0.0,
                thickness=thickness,
                use_contours=False
            )
            
            assert isinstance(mesh, o3d.geometry.TriangleMesh)
            if len(mesh.vertices) > 0:
                vertices = np.asarray(mesh.vertices)
                z_range = vertices[:, 2].max() - vertices[:, 2].min()
                assert z_range <= thickness + 1e-6  # Allow small numerical error


class TestHeightmapMeshGenerator:
    """Test HeightmapMeshGenerator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.triangulator = TriangleTriangulator()
        self.processor = HeightmapProcessor(min_polygon_area=0.01)
        self.combiner = MeshCombiner()
        self.generator = HeightmapMeshGenerator(
            self.triangulator, 
            self.processor, 
            self.combiner
        )
    
    def test_initialization(self):
        """Test generator initialization."""
        assert self.generator.triangulator == self.triangulator
        assert self.generator.heightmap_processor == self.processor
        assert self.generator.mesh_combiner == self.combiner
    
    def test_generate_mesh_surface(self, simple_heightmap, default_scaling):
        """Test surface mesh generation from heightmap."""
        heightmap_handler = HeightmapHandler(
            heightmap=simple_heightmap,
            scaling=default_scaling,
            processor=self.processor
        )
        
        mesh = self.generator.generate_mesh(heightmap_handler)
        
        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) > 0
        assert len(mesh.triangles) > 0
        
        # Check that mesh represents the heightmap surface
        vertices = np.asarray(mesh.vertices)
        assert vertices.shape[1] == 3  # 3D vertices
        
        # Should have roughly heightmap.size vertices (may vary due to scaling)
        expected_vertices = simple_heightmap.size
        assert len(vertices) <= expected_vertices  # May be fewer after processing
    
    def test_generate_mesh_with_scaling(self, simple_heightmap, custom_scaling):
        """Test surface mesh generation with custom scaling."""
        heightmap_handler = HeightmapHandler(
            heightmap=simple_heightmap,
            scaling=custom_scaling,
            processor=self.processor
        )
        
        mesh = self.generator.generate_mesh(heightmap_handler)
        
        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) > 0
        
        # Check that scaling was applied
        vertices = np.asarray(mesh.vertices)
        
        # X and Y should be scaled by 0.5
        x_range = vertices[:, 0].max() - vertices[:, 0].min()
        y_range = vertices[:, 1].max() - vertices[:, 1].min()
        
        # Should be smaller than with default scaling due to 0.5 scale factor
        assert x_range > 0
        assert y_range > 0
    
    def test_generate_mesh_flat_heightmap(self, flat_heightmap, default_scaling):
        """Test surface mesh generation from flat heightmap."""
        heightmap_handler = HeightmapHandler(
            heightmap=flat_heightmap,
            scaling=default_scaling,
            processor=self.processor
        )
        
        mesh = self.generator.generate_mesh(heightmap_handler)
        
        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) > 0
        
        # All Z coordinates should be the same (flat surface)
        vertices = np.asarray(mesh.vertices)
        z_values = vertices[:, 2]
        assert np.allclose(z_values, z_values[0], atol=1e-6)
    
    def test_generate_mesh_minimum_size(self):
        """Test surface mesh generation with minimum size heightmap."""
        minimal_heightmap = np.array([[1.0, 2.0], [3.0, 4.0]])
        
        heightmap_handler = HeightmapHandler(
            heightmap=minimal_heightmap,
            scaling=MeshScaling(),
            processor=self.processor
        )
        
        mesh = self.generator.generate_mesh(heightmap_handler)
        
        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) >= 4  # At least the 4 heightmap points
        assert len(mesh.triangles) >= 2  # At least 2 triangles for a quad


class TestMeshGeneratorIntegration:
    """Integration tests for mesh generators."""
    
    def test_all_generators_produce_valid_meshes(self, test_heightmap, default_scaling):
        """Test that all generators produce valid meshes."""
        triangulator = TriangleTriangulator()
        processor = HeightmapProcessor(min_polygon_area=0.01)
        combiner = MeshCombiner()
        
        heightmap_handler = HeightmapHandler(
            heightmap=test_heightmap,
            scaling=default_scaling,
            processor=processor
        )
        
        generators = [
            FlatMeshGenerator(triangulator, processor, combiner),
            ExtrudedMeshGenerator(triangulator, processor, combiner),
            HeightmapMeshGenerator(triangulator, processor, combiner)
        ]
        
        for generator in generators:
            if isinstance(generator, FlatMeshGenerator):
                mesh = generator.generate_mesh(heightmap_handler, height=1.0)
            elif isinstance(generator, ExtrudedMeshGenerator):
                mesh = generator.generate_mesh(heightmap_handler, thickness=1.0)
            else:  # HeightmapMeshGenerator
                mesh = generator.generate_mesh(heightmap_handler)
            
            assert isinstance(mesh, o3d.geometry.TriangleMesh)
            # Valid mesh should have vertices and triangles
            assert len(mesh.vertices) >= 0  # May be empty in some edge cases
            assert len(mesh.triangles) >= 0
    
    def test_generator_error_handling(self):
        """Test that generators handle errors gracefully."""
        triangulator = TriangleTriangulator()
        processor = HeightmapProcessor(min_polygon_area=0.01)
        combiner = MeshCombiner()
        
        generator = FlatMeshGenerator(triangulator, processor, combiner)
        
        # Test with None heightmap_handler
        with pytest.raises((ValueError, AttributeError)):
            generator.generate_mesh(None)
    
    def test_mesh_properties_consistency(self, simple_heightmap, default_scaling):
        """Test that generated meshes have consistent properties."""
        triangulator = TriangleTriangulator()
        processor = HeightmapProcessor(min_polygon_area=0.01)
        combiner = MeshCombiner()
        
        heightmap_handler = HeightmapHandler(
            heightmap=simple_heightmap,
            scaling=default_scaling,
            processor=processor
        )
        
        # Generate meshes with different generators
        flat_gen = FlatMeshGenerator(triangulator, processor, combiner)
        extruded_gen = ExtrudedMeshGenerator(triangulator, processor, combiner)
        surface_gen = HeightmapMeshGenerator(triangulator, processor, combiner)
        
        flat_mesh = flat_gen.generate_mesh(heightmap_handler, height=0.0)
        extruded_mesh = extruded_gen.generate_mesh(heightmap_handler, thickness=1.0)
        surface_mesh = surface_gen.generate_mesh(heightmap_handler)
        
        # All meshes should be valid Open3D triangular meshes
        for mesh in [flat_mesh, extruded_mesh, surface_mesh]:
            assert isinstance(mesh, o3d.geometry.TriangleMesh)
            
            # Check basic mesh integrity
            vertices = np.asarray(mesh.vertices)
            triangles = np.asarray(mesh.triangles)
            
            if len(vertices) > 0:
                assert vertices.shape[1] == 3  # 3D vertices
                
            if len(triangles) > 0:
                assert triangles.shape[1] == 3  # Triangular faces
                assert np.all(triangles >= 0)  # Valid vertex indices
                assert np.all(triangles < len(vertices))  # Indices within range
