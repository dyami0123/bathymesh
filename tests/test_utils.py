"""Tests for bathymesh utilities."""
import pytest
import numpy as np

from bathymesh.utils import (
    validate_heightmap, normalize_heightmap, 
    calculate_polygon_stats, create_test_heightmap
)
from bathymesh.data_structures import PolygonStats
from shapely.geometry import Polygon


class TestValidateHeightmap:
    """Test heightmap validation function."""
    
    def test_valid_heightmap(self, test_heightmap):
        """Test validation of valid heightmap."""
        validate_heightmap(test_heightmap)
    
    def test_valid_simple_heightmap(self, simple_heightmap):
        """Test validation of simple heightmap."""
        validate_heightmap(simple_heightmap)
        
    
    def test_invalid_1d_array(self):
        """Test that 1D arrays are rejected."""
        with pytest.raises(ValueError, match="must be 2D"):
            validate_heightmap(np.array([1, 2, 3]))
    
    def test_invalid_3d_array(self):
        """Test that 3D arrays are rejected."""
        with pytest.raises(ValueError, match="must be 2D"):
            validate_heightmap(np.random.random((5, 5, 3)))
    
    def test_empty_array(self):
        """Test that empty arrays are rejected."""
        with pytest.raises(ValueError):
            validate_heightmap(np.array([]))
    
    def test_nan_values(self, invalid_heightmap):
        """Test that NaN values are rejected."""
        with pytest.raises(ValueError, match="non-finite"):
            validate_heightmap(invalid_heightmap)
    
    def test_inf_values(self):
        """Test that infinite values are rejected."""
        heightmap = np.ones((5, 5))
        heightmap[2, 2] = np.inf
        with pytest.raises(ValueError, match="non-finite"):
            validate_heightmap(heightmap)
    
    def test_negative_inf_values(self):
        """Test that negative infinite values are rejected."""
        heightmap = np.ones((5, 5))
        heightmap[2, 2] = -np.inf
        with pytest.raises(ValueError, match="non-finite"):
            validate_heightmap(heightmap)
    
    def test_single_pixel(self):
        """Test heightmap with single pixel."""
        heightmap = np.array([[1.0]])
        validate_heightmap(heightmap)
    
    def test_minimum_size(self):
        """Test heightmap with minimum practical size."""
        heightmap = np.ones((2, 2))
        validate_heightmap(heightmap)



class TestNormalizeHeightmap:
    """Test heightmap normalization function."""
    
    def test_normalize_range_0_1(self):
        """Test normalization to 0-1 range."""
        heightmap = np.array([[0, 5, 10], [2, 8, 6]])
        normalized = normalize_heightmap(heightmap, target_range=(0.0, 1.0))
        
        assert normalized.min() == 0.0
        assert normalized.max() == 1.0
        assert normalized.shape == heightmap.shape
    
    def test_normalize_default_range(self):
        """Test normalization with default range (0-1)."""
        heightmap = np.array([[0, 5, 10], [2, 8, 6]])
        normalized = normalize_heightmap(heightmap)
        
        assert normalized.min() == 0.0
        assert normalized.max() == 1.0
        assert normalized.shape == heightmap.shape
    
    def test_normalize_custom_range(self):
        """Test normalization to custom range."""
        heightmap = np.array([[1, 3, 5], [2, 4, 6]])
        normalized = normalize_heightmap(heightmap, target_range=(-10.0, 10.0))
        
        assert normalized.min() == -10.0
        assert normalized.max() == 10.0
        assert normalized.shape == heightmap.shape
    
    def test_normalize_constant_heightmap(self):
        """Test normalization of constant heightmap."""
        heightmap = np.ones((3, 3)) * 5.0
        normalized = normalize_heightmap(heightmap, target_range=(0.0, 1.0))
        
        # When all values are the same, should return midpoint of target range
        expected_value = (0.0 + 1.0) / 2
        assert normalized.shape == heightmap.shape
        assert not np.any(np.isnan(normalized))
        assert np.allclose(normalized, expected_value)
    
    def test_normalize_preserves_relative_order(self):
        """Test that normalization preserves relative order of values."""
        heightmap = np.array([[1, 5, 3], [8, 2, 6]])
        normalized = normalize_heightmap(heightmap, target_range=(0.0, 10.0))
        
        # Find positions of min and max in original
        min_pos = np.unravel_index(np.argmin(heightmap), heightmap.shape)
        max_pos = np.unravel_index(np.argmax(heightmap), heightmap.shape)
        
        # Check they correspond to min and max in normalized
        assert normalized[min_pos] == 0.0
        assert normalized[max_pos] == 10.0
    
    def test_normalize_negative_values(self):
        """Test normalization with negative input values."""
        heightmap = np.array([[-5, 0, 5], [-2, 3, 1]])
        normalized = normalize_heightmap(heightmap, target_range=(0.0, 1.0))
        
        assert normalized.min() == 0.0
        assert normalized.max() == 1.0
    
    def test_invalid_target_range(self):
        """Test that invalid target ranges raise ValueError."""
        heightmap = np.array([[1, 2, 3], [4, 5, 6]])
        
        # Min >= Max should raise ValueError
        with pytest.raises(ValueError, match="Target range min must be less than max"):
            normalize_heightmap(heightmap, target_range=(1.0, 1.0))
        
        with pytest.raises(ValueError, match="Target range min must be less than max"):
            normalize_heightmap(heightmap, target_range=(2.0, 1.0))

