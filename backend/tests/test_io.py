"""Tests for bathymesh I/O operations."""

import pytest
import numpy as np
import open3d as o3d
from pathlib import Path

from bathy.io import export_mesh, get_mesh_info
from bathy.data_structures import MeshInfo, MeshFormat


class TestExportMesh:
    """Test mesh export functionality."""

    def test_export_stl(self, temp_output_dir):
        """Test exporting mesh to STL format."""
        # Create a simple triangle mesh
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        triangles = np.array([[0, 1, 2]])

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(triangles)
        mesh.compute_vertex_normals()

        output_path = temp_output_dir / "test.stl"
        result = export_mesh(mesh, output_path)

        assert result is True
        assert output_path.exists()
        assert output_path.suffix == ".stl"

    def test_export_ply(self, temp_output_dir):
        """Test exporting mesh to PLY format."""
        # Create a simple triangle mesh
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        triangles = np.array([[0, 1, 2]])

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(triangles)

        output_path = temp_output_dir / "test.ply"
        result = export_mesh(mesh, output_path)

        assert result is True
        assert output_path.exists()
        assert output_path.suffix == ".ply"

    def test_export_obj(self, temp_output_dir):
        """Test exporting mesh to OBJ format."""
        # Create a simple triangle mesh
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        triangles = np.array([[0, 1, 2]])

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(triangles)

        output_path = temp_output_dir / "test.obj"
        result = export_mesh(mesh, output_path)

        assert result is True
        assert output_path.exists()
        assert output_path.suffix == ".obj"

    def test_empty_mesh_raises_error(self, temp_output_dir):
        """Test that exporting empty mesh raises ValueError."""
        empty_mesh = o3d.geometry.TriangleMesh()
        output_path = temp_output_dir / "empty.stl"

        with pytest.raises(ValueError, match="Cannot export empty mesh"):
            export_mesh(empty_mesh, output_path)

    def test_unsupported_format_raises_error(self, temp_output_dir):
        """Test that unsupported format raises ValueError."""
        # Create a simple triangle mesh
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        triangles = np.array([[0, 1, 2]])

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(triangles)

        output_path = temp_output_dir / "test.unsupported"

        with pytest.raises(ValueError, match="Unsupported"):
            export_mesh(mesh, output_path)

    def test_directory_creation(self, temp_output_dir):
        """Test that output directories are created if they don't exist."""
        # Create a simple triangle mesh
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        triangles = np.array([[0, 1, 2]])

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(triangles)
        mesh.compute_vertex_normals()

        # Use nested directory that doesn't exist
        output_path = temp_output_dir / "nested" / "directory" / "test.stl"
        result = export_mesh(mesh, output_path)

        assert result is True
        assert output_path.exists()
        assert output_path.parent.exists()


class TestGetMeshInfo:
    """Test mesh information extraction."""

    def test_simple_triangle_mesh_info(self):
        """Test getting info from simple triangle mesh."""
        # Create a simple triangle mesh
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        triangles = np.array([[0, 1, 2]])

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(triangles)

        info = get_mesh_info(mesh)

        assert isinstance(info, MeshInfo)
        assert info.num_vertices == 3
        assert info.num_triangles == 1

    def test_cube_mesh_info(self):
        """Test getting info from cube mesh."""
        # Create a cube mesh
        mesh = o3d.geometry.TriangleMesh.create_box(width=1.0, height=1.0, depth=1.0)

        info = get_mesh_info(mesh)

        assert isinstance(info, MeshInfo)
        assert info.num_vertices == 8  # Cube has 8 vertices
        assert info.num_triangles == 12  # Cube has 12 triangles
        # Cube should be watertight
        assert info.is_watertight is True
        # Bounding box should be approximately 1x1x1
        np.testing.assert_array_almost_equal(
            info.bounding_box_min, [0.0, 0.0, 0.0], decimal=5
        )
        np.testing.assert_array_almost_equal(
            info.bounding_box_max, [1.0, 1.0, 1.0], decimal=5
        )
        np.testing.assert_array_almost_equal(
            info.bounding_box_extent, [1.0, 1.0, 1.0], decimal=5
        )

    def test_sphere_mesh_info(self):
        """Test getting info from sphere mesh."""
        # Create a sphere mesh
        mesh = o3d.geometry.TriangleMesh.create_sphere(radius=1.0, resolution=20)

        info = get_mesh_info(mesh)

        assert isinstance(info, MeshInfo)
        assert info.num_vertices > 0
        assert info.num_triangles > 0
        # Sphere should be watertight (approximately)
        assert info.is_watertight is True

    def test_empty_mesh_info(self):
        """Test getting info from empty mesh."""
        empty_mesh = o3d.geometry.TriangleMesh()
        with pytest.raises(ValueError, match="Cannot get info from empty mesh"):
            get_mesh_info(empty_mesh)

    def test_mesh_info_fields(self):
        """Test that mesh info contains all expected fields and types."""
        # Create a simple triangle mesh
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        triangles = np.array([[0, 1, 2]])

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(triangles)

        info = get_mesh_info(mesh)

        # Check all expected fields exist
        assert hasattr(info, "num_vertices")
        assert hasattr(info, "num_triangles")
        assert hasattr(info, "has_vertex_normals")
        assert hasattr(info, "has_triangle_normals")
        assert hasattr(info, "is_watertight")
        assert hasattr(info, "is_orientable")
        assert hasattr(info, "bounding_box_min")
        assert hasattr(info, "bounding_box_max")
        assert hasattr(info, "bounding_box_extent")

        # Check field types
        assert isinstance(info.num_vertices, int)
        assert isinstance(info.num_triangles, int)
        assert isinstance(info.has_vertex_normals, bool)
        assert isinstance(info.has_triangle_normals, bool)
        assert isinstance(info.is_watertight, bool)
        assert isinstance(info.is_orientable, bool)
        assert isinstance(info.bounding_box_min, list) or info.bounding_box_min is None
        assert isinstance(info.bounding_box_max, list) or info.bounding_box_max is None
        assert (
            isinstance(info.bounding_box_extent, list)
            or info.bounding_box_extent is None
        )

    def test_non_watertight_mesh(self):
        """Test info from non-watertight mesh (single triangle)."""
        # Single triangle is not watertight
        vertices = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]])
        triangles = np.array([[0, 1, 2]])

        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices)
        mesh.triangles = o3d.utility.Vector3iVector(triangles)

        info = get_mesh_info(mesh)

        assert info.is_watertight is False
