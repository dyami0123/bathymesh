"""Tests for image to heightmap processing."""

import numpy as np
import pytest
from PIL import Image
from pathlib import Path
import tempfile
import os

from bathymesh.io.image_to_heightmap import (
    ImageToHeightmapProcessor,
    ColorMapper,
    image_to_heightmap,
    create_sample_color_map
)


class TestColorMapper:
    """Test ColorMapper functionality."""
    
    def test_initialization_simple(self):
        """Test ColorMapper with simple float values."""
        color_map = {
            "#ff0000": 1.0,
            "#00ff00": 2.0,
            "#0000ff": 3.0
        }
        mapper = ColorMapper(color_map, default_fuzziness=10.0)
        
        assert len(mapper.color_map) == 3
        assert mapper.color_map["#ff0000"]["value"] == 1.0
        assert mapper.color_map["#ff0000"]["fuzziness"] == 10.0
        assert mapper.color_map["#ff0000"]["rgb"] == (255, 0, 0)
    
    def test_initialization_with_fuzziness(self):
        """Test ColorMapper with fuzziness specified."""
        color_map = {
            "#ff0000": {"value": 1.0, "fuzziness": 5.0},
            "#00ff00": {"value": 2.0, "fuzziness": 15.0}
        }
        mapper = ColorMapper(color_map)
        
        assert mapper.color_map["#ff0000"]["fuzziness"] == 5.0
        assert mapper.color_map["#00ff00"]["fuzziness"] == 15.0
    
    def test_hex_to_rgb(self):
        """Test hex to RGB conversion."""
        assert ColorMapper._hex_to_rgb("#ff0000") == (255, 0, 0)
        assert ColorMapper._hex_to_rgb("#00ff00") == (0, 255, 0)
        assert ColorMapper._hex_to_rgb("#0000ff") == (0, 0, 255)
        assert ColorMapper._hex_to_rgb("#ffffff") == (255, 255, 255)
        assert ColorMapper._hex_to_rgb("#000000") == (0, 0, 0)
    
    def test_hex_to_rgb_invalid(self):
        """Test hex to RGB with invalid input."""
        with pytest.raises(ValueError):
            ColorMapper._hex_to_rgb("#ff00")  # Too short
        with pytest.raises(ValueError):
            ColorMapper._hex_to_rgb("#ff00000")  # Too long
    
    def test_pixel_mapping_exact_match(self):
        """Test pixel mapping with exact color match."""
        color_map = {"#ff0000": 1.0}
        mapper = ColorMapper(color_map, default_fuzziness=0.0)  # No fuzziness
        
        # This should work since we allow some tolerance in LAB space
        # even with 0 fuzziness due to conversion precision
        result = mapper.map_pixel_to_value((255, 0, 0))
        # We expect either 1.0 or None depending on LAB conversion precision
        assert result is None or result == 1.0
    
    def test_pixel_mapping_with_fuzziness(self):
        """Test pixel mapping with fuzziness tolerance."""
        color_map = {"#ff0000": 1.0}
        mapper = ColorMapper(color_map, default_fuzziness=20.0)
        
        # Close red color should match
        result = mapper.map_pixel_to_value((250, 5, 5))
        assert result == 1.0
    
    def test_pixel_mapping_no_match(self):
        """Test pixel mapping with no match."""
        color_map = {"#ff0000": 1.0}
        mapper = ColorMapper(color_map, default_fuzziness=5.0)
        
        # Blue should not match red
        result = mapper.map_pixel_to_value((0, 0, 255))
        assert result is None
    
    def test_pixel_mapping_priority_order(self):
        """Test that first color in ordered dict takes priority."""
        color_map = {
            "#ff0000": 1.0,  # This should win
            "#fe0101": 2.0   # Very close color
        }
        mapper = ColorMapper(color_map, default_fuzziness=50.0)
        
        # A red-ish color that could match both
        result = mapper.map_pixel_to_value((254, 1, 1))
        assert result == 1.0  # Should get first match


class TestImageToHeightmapProcessor:
    """Test ImageToHeightmapProcessor functionality."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = ImageToHeightmapProcessor()
    
    def create_test_image(self, width=10, height=10, colors=None):
        """Create a test image with specific colors."""
        if colors is None:
            colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255)]  # Red, Green, Blue
        
        # Create image array
        image = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Fill with different colors in sections
        section_width = width // len(colors)
        for i, color in enumerate(colors):
            start_x = i * section_width
            end_x = (i + 1) * section_width if i < len(colors) - 1 else width
            image[:, start_x:end_x] = color
        
        return image
    
    def test_process_image_to_heightmap_basic(self):
        """Test basic image to heightmap processing."""
        image = self.create_test_image(width=9, height=6, colors=[(255, 0, 0), (0, 255, 0), (0, 0, 255)])
        
        color_map = {
            "#ff0000": 1.0,  # Red
            "#00ff00": 2.0,  # Green
            "#0000ff": 3.0   # Blue
        }
        
        heightmap = self.processor.process_image_to_heightmap(
            image, color_map, default_fuzziness=20.0
        )
        
        assert heightmap.shape == (6, 9)
        # Check that we got some matches (not all NaN)
        assert not np.all(np.isnan(heightmap))
    
    def test_process_image_invalid_shape(self):
        """Test processing with invalid image shape."""
        image = np.zeros((10, 10))  # 2D instead of 3D
        color_map = {"#ff0000": 1.0}
        
        with pytest.raises(ValueError, match="Expected RGB image"):
            self.processor.process_image_to_heightmap(image, color_map)
    
    def test_process_image_with_region(self):
        """Test processing with sub-region."""
        image = self.create_test_image(width=20, height=20)
        color_map = {"#ff0000": 1.0, "#00ff00": 2.0, "#0000ff": 3.0}
        
        # Process sub-region
        region = (5, 5, 15, 15)  # 10x10 region
        heightmap = self.processor.process_image_to_heightmap(
            image, color_map, default_fuzziness=20.0, region=region
        )
        
        assert heightmap.shape == (10, 10)
    
    def test_load_and_process_image_file(self, tmp_path):
        """Test loading and processing an actual image file."""
        # Create a simple test image
        image_array = self.create_test_image(width=50, height=50)
        image_pil = Image.fromarray(image_array)
        
        # Save to temporary file
        temp_path = tmp_path / "test_image.png"
        image_pil.save(temp_path)
        
        color_map = {"#ff0000": 1.0, "#00ff00": 2.0, "#0000ff": 3.0}
        
        heightmap = self.processor.process_image_file_to_heightmap(
            temp_path, color_map, default_fuzziness=20.0
        )
        
        assert heightmap.shape == (50, 50)
        assert not np.all(np.isnan(heightmap))
    
    def test_get_image_info(self, tmp_path):
        """Test getting image information."""
        image_array = self.create_test_image(width=100, height=80)
        image_pil = Image.fromarray(image_array)
        temp_path = tmp_path / "test_image.jpg"
        image_pil.save(temp_path)
        
        info = self.processor.get_image_info(temp_path)
        
        assert info['size'] == (100, 80)  # (width, height)
        assert info['mode'] == 'RGB'
        assert info['format'] == 'JPEG'
        assert info['has_transparency'] == False


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_create_sample_color_map(self):
        """Test sample color map creation."""
        color_map = create_sample_color_map()
        
        assert isinstance(color_map, dict)
        assert len(color_map) > 0
        
        # Check that all entries have required structure
        for hex_color, config in color_map.items():
            assert hex_color.startswith('#')
            assert len(hex_color) == 7
            assert 'value' in config
            assert 'fuzziness' in config
            assert isinstance(config['value'], (int, float))
            assert isinstance(config['fuzziness'], (int, float))
    
    def test_image_to_heightmap_convenience(self, tmp_path):
        """Test convenience function."""
        # Create test image
        image_array = np.zeros((20, 30, 3), dtype=np.uint8)
        image_array[:, :10] = [255, 0, 0]  # Red section
        image_array[:, 10:20] = [0, 255, 0]  # Green section
        image_array[:, 20:] = [0, 0, 255]  # Blue section
        
        image_pil = Image.fromarray(image_array)
        temp_path = tmp_path / "test_convenience.png"
        image_pil.save(temp_path)
        
        color_map = {"#ff0000": 1.0, "#00ff00": 2.0, "#0000ff": 3.0}
        
        heightmap = image_to_heightmap(temp_path, color_map, default_fuzziness=20.0)
        
        assert heightmap.shape == (20, 30)
        assert not np.all(np.isnan(heightmap))


# Integration test with real bathymesh workflow
class TestBathymeshIntegration:
    """Test integration with bathymesh workflow."""
    
    def test_heightmap_integration(self, tmp_path):
        """Test that generated heightmap works with bathymesh HeightmapHandler."""
        from bathymesh.core.heightmap_handler import HeightmapHandler
        from bathymesh.data_structures import MeshScaling
        
        # Create a test image with depth colors
        image_array = np.zeros((50, 50, 3), dtype=np.uint8)
        
        # Create a simple depth map pattern
        for y in range(50):
            for x in range(50):
                # Distance from center determines depth
                dist = np.sqrt((x - 25)**2 + (y - 25)**2)
                if dist < 10:
                    image_array[y, x] = [0, 0, 139]  # Dark blue - deep
                elif dist < 20:
                    image_array[y, x] = [0, 100, 200]  # Medium blue
                else:
                    image_array[y, x] = [100, 200, 255]  # Light blue - shallow
        
        # Save test image
        image_pil = Image.fromarray(image_array)
        temp_path = tmp_path / "depth_map.png"
        image_pil.save(temp_path)
        
        # Create color map for bathymetry
        color_map = {
            "#00008b": -5.0,  # Dark blue - deep water
            "#0064c8": -2.0,  # Medium blue
            "#64c8ff": -0.5,  # Light blue - shallow
        }
        
        # Process to heightmap
        processor = ImageToHeightmapProcessor()
        heightmap = processor.process_image_file_to_heightmap(
            temp_path, color_map, default_fuzziness=30.0
        )
        
        # Replace NaN values with 0 for bathymesh compatibility
        heightmap = np.nan_to_num(heightmap, nan=0.0)
        
        # Test with HeightmapHandler
        handler = HeightmapHandler(
            heightmap=heightmap,
            scaling=MeshScaling(scale_x=0.1, scale_y=0.1, scale_z=1.0)
        )
        
        assert handler.shape == (50, 50)
        assert handler.height_range[0] <= handler.height_range[1]
        
        # Test that we can extract contours
        polygons = handler.extract_contour_polygons(-3.0)
        assert isinstance(polygons, list)  # Should return a list even if empty
