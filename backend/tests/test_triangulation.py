"""Tests for bathymesh triangulation module."""
import pytest
import numpy as np
from unittest.mock import Mock, patch
from shapely.geometry import Polygon

from bathymesh.triangulation import BaseTriangulator, TriangleTriangulator, GmshTriangulator


class TestBaseTriangulator:
    """Test base triangulator interface."""
    
    def test_is_abstract(self):
        """Test that BaseTriangulator cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTriangulator()
    
class TestTriangleTriangulator:
    """Test Triangle library triangulator."""
    
    def test_initialization_default(self):
        """Test triangulator initialization with default parameters."""
        triangulator = TriangleTriangulator()
        
        assert triangulator.quality_mesh is True
    
    def test_initialization_custom(self):
        """Test triangulator initialization with custom parameters."""
        triangulator = TriangleTriangulator(quality_mesh=False)
        
        assert triangulator.quality_mesh is False
    
    def test_triangulate_simple_square(self):
        """Test triangulation of simple square polygon."""
        triangulator = TriangleTriangulator()
        
        # Simple unit square polygon
        square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        
        vertices, triangles = triangulator.triangulate_polygon(square)
        
        # Check output format
        assert isinstance(vertices, np.ndarray)
        assert isinstance(triangles, np.ndarray)
        assert vertices.shape[1] == 2  # 2D points
        assert triangles.shape[1] == 3  # Triangles
        
        # Should have at least the original points
        assert len(vertices) >= 4  # Square has 4 vertices
        assert len(triangles) >= 2  # Square needs at least 2 triangles
    
    def test_triangulate_triangle(self):
        """Test triangulation of simple triangle."""
        triangulator = TriangleTriangulator()
        
        # Simple triangle polygon
        triangle_poly = Polygon([(0, 0), (1, 0), (0.5, 1)])
        
        vertices, triangles = triangulator.triangulate_polygon(triangle_poly)
        
        # Should return at least one triangle
        assert len(triangles) >= 1
        assert len(vertices) >= 3
    
    def test_triangulate_with_holes(self):
        """Test triangulation with holes."""
        triangulator = TriangleTriangulator()
        
        # Outer square with inner square hole
        outer_coords = [(0, 0), (2, 0), (2, 2), (0, 2)]
        inner_coords = [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]
        
        # Create polygon with hole
        polygon_with_hole = Polygon(outer_coords, [inner_coords])
        
        vertices, triangles = triangulator.triangulate_polygon(polygon_with_hole)
        
        # Should have triangulation of the area between outer and inner squares
        assert len(triangles) > 0
        assert len(vertices) >= 8  # At least outer (4) + inner (4) vertices
    
    def test_triangulate_quality_mesh(self):
        """Test quality mesh generation."""
        triangulator = TriangleTriangulator(quality_mesh=True)
        
        # Simple square
        square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        
        vertices, triangles = triangulator.triangulate_polygon(square)
        
        # Quality mesh should potentially add Steiner points
        assert len(vertices) >= 4  # At least the original vertices
        assert len(triangles) >= 2  # At least 2 triangles for a square
    
    def test_triangulate_no_quality_mesh(self):
        """Test triangulation without quality mesh generation."""
        triangulator = TriangleTriangulator(quality_mesh=False)
        
        # Simple square
        square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        
        vertices, triangles = triangulator.triangulate_polygon(square)
        
        # Without quality mesh, should use minimal triangulation
        assert len(vertices) >= 4  # At least the original vertices
        assert len(triangles) >= 2  # At least 2 triangles for a square
    
    def test_empty_input_handling(self):
        """Test handling of empty input."""
        triangulator = TriangleTriangulator()
        
        # Empty polygon should raise an error
        with pytest.raises(ValueError):
            empty_polygon = Polygon()
            triangulator.triangulate_polygon(empty_polygon)
    
    def test_invalid_polygon_handling(self):
        """Test handling of invalid polygon."""
        triangulator = TriangleTriangulator()
        
        # Self-intersecting polygon (figure-8 shape)
        invalid_coords = [(0, 0), (1, 1), (1, 0), (0, 1)]
        invalid_polygon = Polygon(invalid_coords)
        
        with pytest.raises(ValueError, match="Input polygon is not valid"):
            triangulator.triangulate_polygon(invalid_polygon)
    
    def test_degenerate_polygon_handling(self):
        """Test handling of degenerate polygon (collinear points)."""
        triangulator = TriangleTriangulator()
        
        # All points on a line (degenerate polygon)
        degenerate_coords = [(0, 0), (1, 0), (2, 0), (3, 0)]
        degenerate_polygon = Polygon(degenerate_coords)
        
        # This should either handle gracefully or raise appropriate error
        try:
            vertices, triangles = triangulator.triangulate_polygon(degenerate_polygon)
            # If it succeeds, check the output is valid
            assert isinstance(vertices, np.ndarray)
            assert isinstance(triangles, np.ndarray)
        except (ValueError, RuntimeError):
            # It's acceptable to raise an error for degenerate cases
            pass
    
    def test_multiple_polygon_error(self):
        """Test that multiple polygons raise an appropriate error."""
        triangulator = TriangleTriangulator()
        
        # Create list of multiple polygons
        polygon1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        polygon2 = Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])
        
        with pytest.raises(ValueError, match="Multiple polygon triangulation not yet implemented"):
            triangulator.triangulate_polygon([polygon1, polygon2])
    
    def test_large_polygon(self):
        """Test triangulation of larger polygon."""
        triangulator = TriangleTriangulator()
        
        # Create a larger polygon (octagon)
        n_sides = 8
        angles = np.linspace(0, 2*np.pi, n_sides, endpoint=False)
        coords = [(np.cos(angle), np.sin(angle)) for angle in angles]
        octagon = Polygon(coords)
        
        vertices, triangles = triangulator.triangulate_polygon(octagon)
        
        assert len(vertices) >= n_sides
        assert len(triangles) >= n_sides - 2  # Polygon triangulation creates n-2 triangles minimum
    
    @patch('bathymesh.triangulation.triangle_triangulator.tr')
    def test_triangle_library_call(self, mock_triangle):
        """Test that triangle library is called with correct parameters."""
        # Mock the triangle library response
        mock_triangle.triangulate.return_value = {
            'vertices': np.array([[0, 0], [1, 0], [1, 1], [0, 1]]),
            'triangles': np.array([[0, 1, 2], [0, 2, 3]])
        }
        
        triangulator = TriangleTriangulator(quality_mesh=True)
        
        square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        
        vertices, triangles = triangulator.triangulate_polygon(square)
        
        # Verify triangle library was called
        mock_triangle.triangulate.assert_called_once()
        
        # Check that the call included expected options
        call_args = mock_triangle.triangulate.call_args
        input_dict = call_args[0][0]
        options = call_args[0][1]
        
        assert 'vertices' in input_dict
        assert 'segments' in input_dict
        assert 'p' in options  # PSLG flag
        assert 'q' in options  # Quality mesh


class TestGmshTriangulator:
    """Test GMSH triangulator."""
    
    def test_initialization(self):
        """Test triangulator initialization."""
        triangulator = GmshTriangulator()
        assert triangulator is not None
        assert isinstance(triangulator, BaseTriangulator)
    
    def test_triangulate_simple_square(self):
        """Test triangulation of simple square polygon."""
        triangulator = GmshTriangulator()
        
        # Simple unit square polygon
        square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        
        vertices, triangles = triangulator.triangulate_polygon(square)
        
        # Check output format
        assert isinstance(vertices, np.ndarray)
        assert isinstance(triangles, np.ndarray)
        assert vertices.shape[1] == 2  # 2D points
        assert triangles.shape[1] == 3  # Triangles
        
        # Should have at least the original points
        assert len(vertices) >= 4  # Square has 4 vertices
        assert len(triangles) >= 2  # Square needs at least 2 triangles
        
        # Verify all triangle indices are valid
        assert np.all(triangles >= 0)
        assert np.all(triangles < len(vertices))
    
    def test_triangulate_triangle(self):
        """Test triangulation of simple triangle."""
        triangulator = GmshTriangulator()
        
        # Simple triangle polygon
        triangle_poly = Polygon([(0, 0), (1, 0), (0.5, 1)])
        
        vertices, triangles = triangulator.triangulate_polygon(triangle_poly)
        
        # Should return at least one triangle
        assert len(triangles) >= 1
        assert len(vertices) >= 3
        
        # Verify triangle indices are valid
        assert np.all(triangles >= 0)
        assert np.all(triangles < len(vertices))
    
    def test_triangulate_with_holes(self):
        """Test triangulation with holes."""
        triangulator = GmshTriangulator()
        
        # Outer square with inner square hole
        outer_coords = [(0, 0), (2, 0), (2, 2), (0, 2)]
        inner_coords = [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]
        
        # Create polygon with hole
        polygon_with_hole = Polygon(outer_coords, [inner_coords])
        
        vertices, triangles = triangulator.triangulate_polygon(polygon_with_hole)
        
        # Should have triangulation of the area between outer and inner squares
        assert len(triangles) > 0
        assert len(vertices) >= 8  # At least outer (4) + inner (4) vertices
        
        # Verify triangle indices are valid
        assert np.all(triangles >= 0)
        assert np.all(triangles < len(vertices))
    
    def test_triangulate_complex_polygon(self):
        """Test triangulation of complex polygon (L-shape)."""
        triangulator = GmshTriangulator()
        
        # L-shaped polygon
        l_coords = [(0, 0), (2, 0), (2, 1), (1, 1), (1, 2), (0, 2)]
        l_polygon = Polygon(l_coords)
        
        vertices, triangles = triangulator.triangulate_polygon(l_polygon)
        
        assert len(triangles) > 0
        assert len(vertices) >= 6  # At least the original vertices
        
        # Verify triangle indices are valid
        assert np.all(triangles >= 0)
        assert np.all(triangles < len(vertices))
    
    def test_triangulate_multipolygon(self):
        """Test triangulation of MultiPolygon."""
        triangulator = GmshTriangulator()
        
        # Create two separate squares
        poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        poly2 = Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])
        
        from shapely.geometry import MultiPolygon
        multipolygon = MultiPolygon([poly1, poly2])
        
        vertices, triangles = triangulator.triangulate_polygon(multipolygon)
        
        # Should triangulate both polygons
        assert len(triangles) >= 4  # At least 2 triangles per square
        assert len(vertices) >= 8  # At least 4 vertices per square
        
        # Verify triangle indices are valid
        assert np.all(triangles >= 0)
        assert np.all(triangles < len(vertices))
    
    def test_triangulate_polygon_list(self):
        """Test triangulation of list of polygons."""
        triangulator = GmshTriangulator()
        
        # Create list of polygons
        poly1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        poly2 = Polygon([(2, 0), (3, 0), (3, 1), (2, 1)])
        polygons = [poly1, poly2]
        
        vertices, triangles = triangulator.triangulate_polygon(polygons)
        
        # Should triangulate both polygons
        assert len(triangles) >= 4  # At least 2 triangles per square
        assert len(vertices) >= 8  # At least 4 vertices per square
        
        # Verify triangle indices are valid
        assert np.all(triangles >= 0)
        assert np.all(triangles < len(vertices))
    
    def test_empty_polygon_handling(self):
        """Test handling of empty polygon."""
        triangulator = GmshTriangulator()
        
        # Empty polygon should raise an error
        with pytest.raises((ValueError, RuntimeError)):
            empty_polygon = Polygon()
            triangulator.triangulate_polygon(empty_polygon)
    
    def test_invalid_polygon_handling(self):
        """Test handling of invalid polygon."""
        triangulator = GmshTriangulator()
        
        # Self-intersecting polygon (figure-8 shape)
        invalid_coords = [(0, 0), (1, 1), (1, 0), (0, 1)]
        invalid_polygon = Polygon(invalid_coords)
        
        # GMSH might handle this differently than Triangle library
        try:
            vertices, triangles = triangulator.triangulate_polygon(invalid_polygon)
            # If it succeeds, verify the output is valid
            assert isinstance(vertices, np.ndarray)
            assert isinstance(triangles, np.ndarray)
        except (ValueError, RuntimeError):
            # It's acceptable to raise an error for invalid polygons
            pass
    
    def test_degenerate_polygon_handling(self):
        """Test handling of degenerate polygon (collinear points)."""
        triangulator = GmshTriangulator()
        
        # All points on a line (degenerate polygon)
        degenerate_coords = [(0, 0), (1, 0), (2, 0), (3, 0)]
        degenerate_polygon = Polygon(degenerate_coords)
        
        # This should either handle gracefully or raise appropriate error
        try:
            vertices, triangles = triangulator.triangulate_polygon(degenerate_polygon)
            # If it succeeds, check the output is valid
            assert isinstance(vertices, np.ndarray)
            assert isinstance(triangles, np.ndarray)
        except (ValueError, RuntimeError):
            # It's acceptable to raise an error for degenerate cases
            pass
    
    def test_large_polygon(self):
        """Test triangulation of larger polygon."""
        triangulator = GmshTriangulator()
        
        # Create a larger polygon (octagon)
        n_sides = 8
        angles = np.linspace(0, 2*np.pi, n_sides, endpoint=False)
        coords = [(np.cos(angle), np.sin(angle)) for angle in angles]
        octagon = Polygon(coords)
        
        vertices, triangles = triangulator.triangulate_polygon(octagon)
        
        assert len(vertices) >= n_sides
        assert len(triangles) >= n_sides - 2  # Polygon triangulation creates n-2 triangles minimum
        
        # Verify triangle indices are valid
        assert np.all(triangles >= 0)
        assert np.all(triangles < len(vertices))
    
    def test_no_triangles_error_handling(self):
        """Test error handling when no triangles are generated."""
        triangulator = GmshTriangulator()
        
        # Use mock to simulate mesh with no triangles
        with patch('pygmsh.geo.Geometry') as mock_geom_context:
            mock_geom = Mock()
            mock_geom_context.return_value.__enter__.return_value = mock_geom
            
            mock_mesh = Mock()
            mock_mesh.points = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]])
            mock_mesh.cells_dict = {}  # No triangles
            mock_geom.generate_mesh.return_value = mock_mesh
            
            square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
            
            with pytest.raises(ValueError, match="No triangles found in mesh"):
                triangulator.triangulate_polygon(square)
    
    @patch('pygmsh.geo.Geometry')
    def test_gmsh_library_call(self, mock_geom_context):
        """Test that GMSH library is called with correct parameters."""
        # Mock the geometry context and mesh generation
        mock_geom = Mock()
        mock_geom_context.return_value.__enter__.return_value = mock_geom
        
        mock_mesh = Mock()
        mock_mesh.points = np.array([[0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0]])
        mock_mesh.cells_dict = {'triangle': np.array([[0, 1, 2], [0, 2, 3]])}
        mock_geom.generate_mesh.return_value = mock_mesh
        
        triangulator = GmshTriangulator()
        square = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])
        
        vertices, triangles = triangulator.triangulate_polygon(square)
        
        # Verify geometry methods were called
        mock_geom.add_polygon.assert_called_once()
        mock_geom.add_physical.assert_called_once()
        mock_geom.generate_mesh.assert_called_once()
        
        # Check that polygon was added with correct parameters
        call_args = mock_geom.add_polygon.call_args
        polygon_points = call_args[0][0]
        
        # Should have added the square's vertices
        assert len(polygon_points) == 5  # 4 vertices + closing point
        assert polygon_points[0] == [0, 0]
        assert polygon_points[1] == [1, 0]
        assert polygon_points[2] == [1, 1]
        assert polygon_points[3] == [0, 1]
        assert polygon_points[4] == [0, 0]  # Closing point
    
    def test_polygon_with_multiple_holes(self):
        """Test triangulation with multiple holes."""
        triangulator = GmshTriangulator()
        
        # Outer square with two inner square holes
        outer_coords = [(0, 0), (4, 0), (4, 2), (0, 2)]
        hole1_coords = [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]
        hole2_coords = [(2.5, 0.5), (3.5, 0.5), (3.5, 1.5), (2.5, 1.5)]
        
        # Create polygon with holes
        polygon_with_holes = Polygon(outer_coords, [hole1_coords, hole2_coords])
        
        vertices, triangles = triangulator.triangulate_polygon(polygon_with_holes)
        
        # Should have triangulation of the area between outer and inner squares
        assert len(triangles) > 0
        assert len(vertices) >= 12  # At least outer (4) + hole1 (4) + hole2 (4) vertices
        
        # Verify triangle indices are valid
        assert np.all(triangles >= 0)
        assert np.all(triangles < len(vertices))
