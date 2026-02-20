"""Tests for mesh splitting functionality."""

import numpy as np
import open3d as o3d
import pytest

from bathy.config import (
    MeshGenerationConfig,
    MeshSplittingConfig,
    SplitPlaneConfig,
)
from bathy.mesh_splitter import MeshSplitter, SplitPlane


class TestSplitPlane:
    """Tests for the SplitPlane dataclass."""

    def test_initialization_normalizes_normal(self):
        """Test that normal vector is normalized on initialization."""
        plane = SplitPlane(origin=(0.0, 0.0, 0.0), normal=(2.0, 0.0, 0.0))
        assert np.allclose(plane.normal, (1.0, 0.0, 0.0))

    def test_initialization_handles_non_unit_normal(self):
        """Test normalization of arbitrary normal vector."""
        plane = SplitPlane(origin=(0.0, 0.0, 0.0), normal=(1.0, 1.0, 0.0))
        expected = np.array([1.0, 1.0, 0.0]) / np.sqrt(2)
        assert np.allclose(plane.normal, expected)

    def test_signed_distance_positive(self):
        """Test signed distance for point on positive side of plane."""
        plane = SplitPlane(origin=(0.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))
        point = np.array([5.0, 0.0, 0.0])
        assert plane.signed_distance(point) == pytest.approx(5.0)

    def test_signed_distance_negative(self):
        """Test signed distance for point on negative side of plane."""
        plane = SplitPlane(origin=(0.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))
        point = np.array([-3.0, 0.0, 0.0])
        assert plane.signed_distance(point) == pytest.approx(-3.0)

    def test_signed_distance_on_plane(self):
        """Test signed distance for point exactly on plane."""
        plane = SplitPlane(origin=(0.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))
        point = np.array([0.0, 5.0, 10.0])
        assert plane.signed_distance(point) == pytest.approx(0.0)

    def test_signed_distance_with_offset_origin(self):
        """Test signed distance with non-zero origin."""
        plane = SplitPlane(origin=(5.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))
        point = np.array([10.0, 0.0, 0.0])
        assert plane.signed_distance(point) == pytest.approx(5.0)

    def test_classify_point_positive(self):
        """Test point classification on positive side."""
        plane = SplitPlane(origin=(0.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))
        assert plane.classify_point(np.array([1.0, 0.0, 0.0])) == 1

    def test_classify_point_negative(self):
        """Test point classification on negative side."""
        plane = SplitPlane(origin=(0.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))
        assert plane.classify_point(np.array([-1.0, 0.0, 0.0])) == -1

    def test_classify_point_on_plane(self):
        """Test point classification exactly on plane."""
        plane = SplitPlane(origin=(0.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))
        assert plane.classify_point(np.array([0.0, 5.0, 10.0])) == 0


class TestMeshSplitter:
    """Tests for the MeshSplitter class."""

    @pytest.fixture
    def simple_cube_mesh(self) -> o3d.geometry.TriangleMesh:
        """Create a simple cube mesh for testing."""
        mesh = o3d.geometry.TriangleMesh.create_box(width=2.0, height=2.0, depth=2.0)
        # Center the cube at origin
        mesh.translate((-1.0, -1.0, -1.0))
        mesh.compute_vertex_normals()
        return mesh

    @pytest.fixture
    def default_splitter(self) -> MeshSplitter:
        """Create a splitter with default (disabled) config."""
        config = MeshSplittingConfig(enabled=False)
        return MeshSplitter(config)

    @pytest.fixture
    def single_plane_splitter(self) -> MeshSplitter:
        """Create a splitter with a single YZ plane at origin."""
        config = MeshSplittingConfig(
            enabled=True,
            planes=[SplitPlaneConfig(origin=(0.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))],
            cap_cut_faces=True,
        )
        return MeshSplitter(config)

    @pytest.fixture
    def grid_splitter(self) -> MeshSplitter:
        """Create a splitter with grid-based splitting (2x2 in XY).

        The cube is centered at origin (-1 to 1), so split at 0.0 on each axis.
        """
        config = MeshSplittingConfig(
            enabled=True,
            planes=[],  # Empty to trigger grid-based
            grid_splits_x=[0.0],  # Split location at x=0
            grid_splits_y=[0.0],  # Split location at y=0
            grid_splits_z=[],  # No z splits
            cap_cut_faces=True,
        )
        return MeshSplitter(config)

    def test_from_config(self):
        """Test MeshSplitter creation from MeshGenerationConfig."""
        config = MeshGenerationConfig()
        splitter = MeshSplitter.from_config(config)
        assert isinstance(splitter, MeshSplitter)
        assert splitter.config.enabled is False

    def test_split_disabled_returns_original(
        self,
        simple_cube_mesh: o3d.geometry.TriangleMesh,
        default_splitter: MeshSplitter,
    ):
        """Test that disabled splitter returns original mesh in list."""
        result = default_splitter.split_mesh(simple_cube_mesh)
        assert len(result) == 1
        assert result[0] is simple_cube_mesh

    def test_no_planes_returns_original(
        self, simple_cube_mesh: o3d.geometry.TriangleMesh
    ):
        """Test that splitter with no planes returns original mesh."""
        config = MeshSplittingConfig(
            enabled=True,
            planes=[],
            grid_splits_x=[],
            grid_splits_y=[],
            grid_splits_z=[],
        )
        splitter = MeshSplitter(config)
        result = splitter.split_mesh(simple_cube_mesh)
        assert len(result) == 1

    def test_single_plane_splits_into_two(
        self,
        simple_cube_mesh: o3d.geometry.TriangleMesh,
        single_plane_splitter: MeshSplitter,
    ):
        """Test that single plane splits mesh into two pieces."""
        result = single_plane_splitter.split_mesh(simple_cube_mesh)
        assert len(result) == 2

    def test_split_pieces_have_vertices(
        self,
        simple_cube_mesh: o3d.geometry.TriangleMesh,
        single_plane_splitter: MeshSplitter,
    ):
        """Test that both split pieces have vertices."""
        result = single_plane_splitter.split_mesh(simple_cube_mesh)
        for piece in result:
            assert len(np.asarray(piece.vertices)) > 0

    def test_split_pieces_have_triangles(
        self,
        simple_cube_mesh: o3d.geometry.TriangleMesh,
        single_plane_splitter: MeshSplitter,
    ):
        """Test that both split pieces have triangles."""
        result = single_plane_splitter.split_mesh(simple_cube_mesh)
        for piece in result:
            assert len(np.asarray(piece.triangles)) > 0

    def test_grid_splitting_creates_correct_pieces(
        self, simple_cube_mesh: o3d.geometry.TriangleMesh, grid_splitter: MeshSplitter
    ):
        """Test that 1x1 grid splitting creates 4 pieces (2 cuts = 4 quadrants)."""
        result = grid_splitter.split_mesh(simple_cube_mesh)
        # 1 cut in X and 1 cut in Y should create 4 pieces
        assert len(result) == 4

    def test_get_split_planes_explicit(
        self,
        single_plane_splitter: MeshSplitter,
        simple_cube_mesh: o3d.geometry.TriangleMesh,
    ):
        """Test that explicit planes are returned correctly."""
        planes = single_plane_splitter.get_split_planes(simple_cube_mesh)
        assert len(planes) == 1
        assert planes[0].origin == (0.0, 0.0, 0.0)
        assert np.allclose(planes[0].normal, (1.0, 0.0, 0.0))

    def test_get_split_planes_grid(
        self, grid_splitter: MeshSplitter, simple_cube_mesh: o3d.geometry.TriangleMesh
    ):
        """Test that grid-based planes are generated correctly."""
        planes = grid_splitter.get_split_planes(simple_cube_mesh)
        # 1 split in X + 1 split in Y = 2 planes
        assert len(planes) == 2

    def test_split_preserves_approximate_volume(
        self,
        simple_cube_mesh: o3d.geometry.TriangleMesh,
        single_plane_splitter: MeshSplitter,
    ):
        """Test that split pieces together have roughly the same volume as original."""
        # This is approximate due to capping and mesh cleanup
        original_bbox = simple_cube_mesh.get_axis_aligned_bounding_box()
        original_extent = np.prod(original_bbox.get_extent())

        result = single_plane_splitter.split_mesh(simple_cube_mesh)

        total_extent = 0
        for piece in result:
            bbox = piece.get_axis_aligned_bounding_box()
            total_extent += np.prod(bbox.get_extent())

        # Allow for some tolerance due to overlapping bounding boxes
        assert total_extent >= original_extent * 0.5

    def test_empty_mesh_returns_empty(self, single_plane_splitter: MeshSplitter):
        """Test that empty mesh input returns empty results."""
        empty_mesh = o3d.geometry.TriangleMesh()
        result = single_plane_splitter.split_mesh(empty_mesh)
        assert len(result) == 0


class TestMeshSplitterCapping:
    """Tests for mesh capping functionality."""

    @pytest.fixture
    def capped_splitter(self) -> MeshSplitter:
        """Create a splitter with capping enabled."""
        config = MeshSplittingConfig(
            enabled=True,
            planes=[SplitPlaneConfig(origin=(0.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))],
            cap_cut_faces=True,
        )
        return MeshSplitter(config)

    @pytest.fixture
    def uncapped_splitter(self) -> MeshSplitter:
        """Create a splitter with capping disabled."""
        config = MeshSplittingConfig(
            enabled=True,
            planes=[SplitPlaneConfig(origin=(0.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))],
            cap_cut_faces=False,
        )
        return MeshSplitter(config)

    @pytest.fixture
    def simple_cube_mesh(self) -> o3d.geometry.TriangleMesh:
        """Create a simple cube mesh for testing."""
        mesh = o3d.geometry.TriangleMesh.create_box(width=2.0, height=2.0, depth=2.0)
        mesh.translate((-1.0, -1.0, -1.0))
        mesh.compute_vertex_normals()
        return mesh

    def test_capped_has_more_triangles(
        self,
        simple_cube_mesh: o3d.geometry.TriangleMesh,
        capped_splitter: MeshSplitter,
        uncapped_splitter: MeshSplitter,
    ):
        """Test that capped meshes have more triangles than uncapped."""
        capped_result = capped_splitter.split_mesh(simple_cube_mesh)
        uncapped_result = uncapped_splitter.split_mesh(simple_cube_mesh)

        capped_triangles = sum(len(np.asarray(m.triangles)) for m in capped_result)
        uncapped_triangles = sum(len(np.asarray(m.triangles)) for m in uncapped_result)

        assert capped_triangles > uncapped_triangles


class TestMeshSplitterEdgeCases:
    """Tests for edge cases in mesh splitting."""

    @pytest.fixture
    def splitter_at_edge(self) -> MeshSplitter:
        """Create a splitter with plane at mesh edge."""
        config = MeshSplittingConfig(
            enabled=True,
            planes=[SplitPlaneConfig(origin=(1.0, 0.0, 0.0), normal=(1.0, 0.0, 0.0))],
            cap_cut_faces=True,
        )
        return MeshSplitter(config)

    @pytest.fixture
    def simple_cube_mesh(self) -> o3d.geometry.TriangleMesh:
        """Create a simple cube mesh for testing (0 to 2 in each dimension)."""
        mesh = o3d.geometry.TriangleMesh.create_box(width=2.0, height=2.0, depth=2.0)
        mesh.compute_vertex_normals()
        return mesh

    def test_plane_at_mesh_edge(
        self,
        simple_cube_mesh: o3d.geometry.TriangleMesh,
        splitter_at_edge: MeshSplitter,
    ):
        """Test splitting when plane passes through mesh edge."""
        # Should still produce valid split
        result = splitter_at_edge.split_mesh(simple_cube_mesh)
        assert len(result) >= 1  # At least one piece should exist

    def test_multiple_planes_same_axis(
        self, simple_cube_mesh: o3d.geometry.TriangleMesh
    ):
        """Test multiple parallel planes along same axis."""
        config = MeshSplittingConfig(
            enabled=True,
            planes=[
                SplitPlaneConfig(origin=(0.5, 0.0, 0.0), normal=(1.0, 0.0, 0.0)),
                SplitPlaneConfig(origin=(1.5, 0.0, 0.0), normal=(1.0, 0.0, 0.0)),
            ],
            cap_cut_faces=True,
        )
        splitter = MeshSplitter(config)
        result = splitter.split_mesh(simple_cube_mesh)
        # 2 parallel cuts should create 3 pieces
        assert len(result) == 3

    def test_diagonal_plane(self, simple_cube_mesh: o3d.geometry.TriangleMesh):
        """Test splitting with diagonal plane."""
        config = MeshSplittingConfig(
            enabled=True,
            planes=[
                SplitPlaneConfig(origin=(1.0, 1.0, 1.0), normal=(1.0, 1.0, 0.0)),
            ],
            cap_cut_faces=True,
        )
        splitter = MeshSplitter(config)
        result = splitter.split_mesh(simple_cube_mesh)
        assert len(result) == 2


@pytest.mark.integration
class TestMeshSplitterIntegration:
    """Integration tests for mesh splitting with full workflow."""

    def test_sphere_split(self):
        """Test splitting a sphere mesh."""
        sphere = o3d.geometry.TriangleMesh.create_sphere(radius=1.0, resolution=10)
        sphere.compute_vertex_normals()

        config = MeshSplittingConfig(
            enabled=True,
            planes=[SplitPlaneConfig(origin=(0.0, 0.0, 0.0), normal=(0.0, 0.0, 1.0))],
            cap_cut_faces=True,
        )
        splitter = MeshSplitter(config)
        result = splitter.split_mesh(sphere)

        assert len(result) == 2
        # Both hemispheres should have roughly similar vertex counts
        v1 = len(np.asarray(result[0].vertices))
        v2 = len(np.asarray(result[1].vertices))
        ratio = min(v1, v2) / max(v1, v2)
        assert ratio > 0.5  # Hemispheres should be relatively balanced

    def test_cylinder_split(self):
        """Test splitting a cylinder mesh."""
        cylinder = o3d.geometry.TriangleMesh.create_cylinder(
            radius=1.0, height=4.0, resolution=20
        )
        cylinder.compute_vertex_normals()

        config = MeshSplittingConfig(
            enabled=True,
            grid_splits_z=[0.0],  # Split at z=0 (middle of cylinder height)
            cap_cut_faces=True,
        )
        splitter = MeshSplitter(config)
        result = splitter.split_mesh(cylinder)

        assert len(result) == 2
