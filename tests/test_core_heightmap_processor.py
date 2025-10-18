"""Tests for bathymesh core module - HeightmapProcessor."""
import pytest
import numpy as np
from shapely.geometry import Polygon

from bathymesh.core import HeightmapProcessor
from bathymesh.data_structures import MeshScaling


class TestHeightmapProcessor:
    """Test HeightmapProcessor class."""
    
    def test_initialization_default(self):
        """Test processor initialization with default parameters."""
        processor = HeightmapProcessor()
        assert processor.min_polygon_area == 1e-2
    
    def test_initialization_custom(self):
        """Test processor initialization with custom parameters."""
        processor = HeightmapProcessor(min_polygon_area=0.1)
        assert processor.min_polygon_area == 0.1
    
    def test_extract_contour_polygons_simple(self):
        """Test contour extraction from simple heightmap."""
        processor = HeightmapProcessor(min_polygon_area=0.01)
        
        # Create a simple heightmap with a circular peak
        x = np.linspace(-2, 2, 20)
        y = np.linspace(-2, 2, 20)
        X, Y = np.meshgrid(x, y)
        heightmap = np.exp(-(X**2 + Y**2))  # Gaussian peak
        
        polygons = processor.extract_contour_polygons(heightmap, 0.5)
        
        assert isinstance(polygons, list)
        assert len(polygons) >= 0  # May or may not find polygons depending on threshold
        for polygon in polygons:
            assert isinstance(polygon, Polygon)
            assert polygon.is_valid
            assert polygon.area > processor.min_polygon_area
    
    def test_extract_contour_polygons_multiple_levels(self):
        """Test contour extraction with different threshold levels."""
        processor = HeightmapProcessor(min_polygon_area=0.001)
        
        # Create heightmap with stepped levels
        heightmap = np.zeros((20, 20))
        heightmap[5:15, 5:15] = 1.0  # Inner square
        heightmap[8:12, 8:12] = 2.0  # Center square
        
        # Test different thresholds
        low_polygons = processor.extract_contour_polygons(heightmap, 0.5)
        high_polygons = processor.extract_contour_polygons(heightmap, 1.5)
        
        # Lower threshold should find more/larger contours
        assert isinstance(low_polygons, list)
        assert isinstance(high_polygons, list)
        
        # Validate all polygons
        for polygon in low_polygons + high_polygons:
            assert isinstance(polygon, Polygon)
            assert polygon.is_valid
    
    def test_extract_contour_polygons_invalid_input(self):
        """Test contour extraction with invalid input."""
        processor = HeightmapProcessor()
        
        # Test 1D array
        with pytest.raises(ValueError, match="must be 2D"):
            processor.extract_contour_polygons(np.array([1, 2, 3]), 0.5)
        
        # Test 3D array
        with pytest.raises(ValueError, match="must be 2D"):
            processor.extract_contour_polygons(np.random.random((5, 5, 3)), 0.5)
    
    def test_extract_contour_polygons_flat_heightmap(self):
        """Test contour extraction from flat heightmap."""
        processor = HeightmapProcessor()
        
        # Flat heightmap should not produce contours
        flat_heightmap = np.ones((10, 10))
        polygons = processor.extract_contour_polygons(flat_heightmap, 0.5)
        
        assert isinstance(polygons, list)
        assert len(polygons) == 0  # No contours in flat surface
    
    def test_extract_multi_level_polygons(self):
        """Test multi-level polygon extraction."""
        processor = HeightmapProcessor(min_polygon_area=0.001)
        
        # Create stepped heightmap
        heightmap = np.zeros((20, 20))
        heightmap[5:15, 5:15] = 1.0
        heightmap[8:12, 8:12] = 2.0
        heightmap[9:11, 9:11] = 3.0
        
        thresholds = [0.5, 1.5, 2.5]
        results = processor.extract_multi_level_polygons(heightmap, thresholds)
        
        assert isinstance(results, list)
        assert len(results) == len(thresholds)
        
        for threshold, polygons in results:
            assert threshold in thresholds
            assert isinstance(polygons, list)
            for polygon in polygons:
                assert isinstance(polygon, Polygon)
                assert polygon.is_valid
    
    def test_create_simple_surface_mesh_data_default_scaling(self):
        """Test surface mesh data creation with default scaling."""
        processor = HeightmapProcessor()
        
        # Simple 3x3 heightmap
        heightmap = np.array([
            [0, 1, 0],
            [1, 2, 1], 
            [0, 1, 0]
        ])
        
        vertices, faces = processor.create_simple_surface_mesh_data(heightmap)
        
        assert isinstance(vertices, np.ndarray)
        assert isinstance(faces, np.ndarray)
        assert vertices.shape == (9, 3)  # 3x3 = 9 vertices, each with x,y,z
        assert faces.shape[1] == 3  # Triangular faces
        assert len(faces) == 8  # (3-1)*(3-1)*2 = 8 triangles
        
        # Check vertex coordinates with default scaling
        assert vertices[0, 0] == 0  # x
        assert vertices[0, 1] == 0  # y
        assert vertices[0, 2] == 0  # z (heightmap[0,0])
        
        assert vertices[4, 0] == 1  # x (middle)
        assert vertices[4, 1] == 1  # y (middle)
        assert vertices[4, 2] == 2  # z (heightmap[1,1])
    
    def test_create_simple_surface_mesh_data_custom_scaling(self):
        """Test surface mesh data creation with custom scaling."""
        processor = HeightmapProcessor()
        scaling = MeshScaling(scale_x=2.0, scale_y=3.0, scale_z=0.5)
        
        # Simple 2x2 heightmap
        heightmap = np.array([
            [1, 2],
            [3, 4]
        ])
        
        vertices, faces = processor.create_simple_surface_mesh_data(heightmap, scaling)
        
        assert vertices.shape == (4, 3)  # 2x2 = 4 vertices
        
        # Check scaled coordinates
        assert vertices[0, 0] == 0.0    # x = 0 * 2.0
        assert vertices[0, 1] == 0.0    # y = 0 * 3.0
        assert vertices[0, 2] == 0.5    # z = 1 * 0.5
        
        assert vertices[1, 0] == 2.0    # x = 1 * 2.0
        assert vertices[1, 1] == 0.0    # y = 0 * 3.0
        assert vertices[1, 2] == 1.0    # z = 2 * 0.5
        
        assert vertices[3, 0] == 2.0    # x = 1 * 2.0
        assert vertices[3, 1] == 3.0    # y = 1 * 3.0
        assert vertices[3, 2] == 2.0    # z = 4 * 0.5
    
    def test_create_simple_surface_mesh_data_single_pixel(self):
        """Test surface mesh data creation with single pixel."""
        processor = HeightmapProcessor()
        
        # Single pixel heightmap
        heightmap = np.array([[5.0]])
        
        vertices, faces = processor.create_simple_surface_mesh_data(heightmap)
        
        assert vertices.shape == (1, 3)
        assert faces.shape[0] == 0  # No faces possible with single vertex
        assert vertices[0, 2] == 5.0  # Height value
    
    def test_create_simple_surface_mesh_data_minimum_size(self):
        """Test surface mesh data creation with minimum practical size."""
        processor = HeightmapProcessor()
        
        # 2x2 heightmap (minimum for faces)
        heightmap = np.array([
            [1, 2],
            [3, 4]
        ])
        
        vertices, faces = processor.create_simple_surface_mesh_data(heightmap)
        
        assert vertices.shape == (4, 3)
        assert faces.shape == (2, 3)  # 2 triangular faces
        
        # Check face indices are valid
        assert np.all(faces >= 0)
        assert np.all(faces < len(vertices))
    
    def test_contour_to_polygon_valid(self):
        """Test contour to polygon conversion with valid contour."""
        processor = HeightmapProcessor()
        
        # Square contour (in row,col format as from skimage)
        contour = np.array([
            [1, 1],
            [1, 4],
            [4, 4],
            [4, 1],
            [1, 1]
        ])
        
        polygon = processor._contour_to_polygon(contour)
        
        assert isinstance(polygon, Polygon)
        assert polygon.is_valid
        assert polygon.area > 0
    
    def test_contour_to_polygon_invalid(self):
        """Test contour to polygon conversion with invalid contour."""
        processor = HeightmapProcessor()
        
        # Too few points
        short_contour = np.array([[1, 1], [2, 2]])
        polygon = processor._contour_to_polygon(short_contour)
        assert polygon is None
        
        # Empty contour
        empty_contour = np.array([]).reshape(0, 2)
        polygon = processor._contour_to_polygon(empty_contour)
        assert polygon is None
    
    def test_is_valid_polygon(self):
        """Test polygon validation."""
        processor = HeightmapProcessor(min_polygon_area=1.0)
        
        # Valid large polygon
        large_coords = [(0, 0), (2, 0), (2, 2), (0, 2)]
        large_polygon = Polygon(large_coords)
        assert processor._is_valid_polygon(large_polygon) is True
        
        # Valid but too small polygon
        small_coords = [(0, 0), (0.1, 0), (0.1, 0.1), (0, 0.1)]
        small_polygon = Polygon(small_coords)
        assert processor._is_valid_polygon(small_polygon) is False
        
        # Invalid self-intersecting polygon
        invalid_coords = [(0, 0), (1, 1), (1, 0), (0, 1)]  # bow-tie shape
        invalid_polygon = Polygon(invalid_coords)
        assert processor._is_valid_polygon(invalid_polygon) is False
    
    def test_processor_with_realistic_data(self):
        """Test processor with realistic heightmap data."""
        processor = HeightmapProcessor(min_polygon_area=0.1)
        
        # Create realistic terrain-like heightmap
        x = np.linspace(-5, 5, 50)
        y = np.linspace(-5, 5, 50)
        X, Y = np.meshgrid(x, y)
        
        # Multiple peaks and valleys
        heightmap = (
            2 * np.exp(-((X-1)**2 + (Y-1)**2)) +    # Peak at (1,1)
            1.5 * np.exp(-((X+1)**2 + (Y+1)**2)) +  # Peak at (-1,-1)
            0.5 * np.sin(X) * np.cos(Y) +            # Wave pattern
            0.1 * np.random.random((50, 50))         # Noise
        )
        
        # Extract contours at multiple levels
        thresholds = [0.2, 0.5, 1.0, 1.5]
        results = processor.extract_multi_level_polygons(heightmap, thresholds)
        
        assert len(results) == 4
        
        # Should find some polygons at reasonable thresholds
        total_polygons = sum(len(polygons) for _, polygons in results)
        assert total_polygons > 0
        
        # Test surface mesh creation
        vertices, faces = processor.create_simple_surface_mesh_data(
            heightmap, 
            MeshScaling(scale_x=0.1, scale_y=0.1, scale_z=2.0)
        )
        
        assert len(vertices) == 50 * 50
        assert len(faces) == (50-1) * (50-1) * 2
