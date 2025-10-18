#!/usr/bin/env python3
"""Test script for the scipy triangulator."""

import numpy as np
from shapely.geometry import Polygon
import matplotlib.pyplot as plt
from bathymesh.triangulation import ScipyTriangulator


def create_test_polygon():
    """Create a simple test polygon."""
    # Create a square with a hole
    exterior = [(0, 0), (10, 0), (10, 10), (0, 10)]
    hole = [(3, 3), (7, 3), (7, 7), (3, 7)]
    return Polygon(exterior, [hole])


def visualize_triangulation(vertices, triangles, polygon, title="Triangulation"):
    """Visualize the triangulation result."""
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))
    
    # Plot triangles
    for triangle in triangles:
        tri_points = vertices[triangle]
        tri_points = np.vstack([tri_points, tri_points[0]])  # Close the triangle
        ax.plot(tri_points[:, 0], tri_points[:, 1], 'b-', alpha=0.6, linewidth=0.5)
    
    # Plot vertices
    ax.scatter(vertices[:, 0], vertices[:, 1], c='red', s=20, zorder=5)
    
    # Plot original polygon boundary
    x, y = polygon.exterior.xy
    ax.plot(x, y, 'k-', linewidth=2, label='Boundary')
    
    # Plot holes
    for interior in polygon.interiors:
        x, y = interior.xy
        ax.plot(x, y, 'k-', linewidth=2)
    
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.legend()
    ax.set_title(title)
    plt.tight_layout()
    plt.savefig(f"triangulation_{title}.png")


def test_scipy_triangulator():
    """Test the scipy triangulator implementation."""
    print("Testing ScipyTriangulator...")
    
    # Create test polygon
    polygon = create_test_polygon()
    print(f"Test polygon area: {polygon.area}")
    print(f"Test polygon is valid: {polygon.is_valid}")
    
    # Test with different configurations
    configs = [
        {"add_interior_points": False, "interior_point_density": 1.0},
        {"add_interior_points": True, "interior_point_density": 0.5},
        {"add_interior_points": True, "interior_point_density": 2.0},
    ]
    
    for i, config in enumerate(configs):
        print(f"\nConfiguration {i+1}: {config}")
        
        triangulator = ScipyTriangulator(**config)
        
        try:
            vertices, triangles = triangulator.triangulate_polygon(polygon)
            
            print(f"  Result: {len(vertices)} vertices, {len(triangles)} triangles")
            print(f"  Vertices shape: {vertices.shape}")
            print(f"  Triangles shape: {triangles.shape}")
            
            # Basic validation
            assert vertices.shape[1] == 2, "Vertices should be 2D"
            assert triangles.shape[1] == 3, "Triangles should have 3 vertices"
            assert np.all(triangles >= 0), "Triangle indices should be non-negative"
            assert np.all(triangles < len(vertices)), "Triangle indices should be valid"
            
            print(f"  ✓ Triangulation successful")
            
            # Visualize (comment out if running headless)
            visualize_triangulation(vertices, triangles, polygon, 
                                   f"Config {i+1}: {config}")
            
        except Exception as e:
            print(f"  ✗ Triangulation failed: {e}")


if __name__ == "__main__":
    test_scipy_triangulator()
