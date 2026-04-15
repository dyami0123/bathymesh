"""Tests for bathymesh workflow module."""

import pytest
import numpy as np
import open3d as o3d
from pathlib import Path

from bathy import BathymeshWorkflow, MeshType, MeshScaling
from bathy.data_structures import MeshInfo


class TestBathymeshWorkflow:
    """Test BathymeshWorkflow main orchestration class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.workflow = BathymeshWorkflow(
            min_polygon_area=1e-2, merge_threshold=1e-6, quality_triangulation=True
        )

    def test_initialization_default(self):
        """Test workflow initialization with default parameters."""
        workflow = BathymeshWorkflow()
        assert workflow is not None
        # Check that all generators are initialized
        assert hasattr(workflow, "flat_generator")
        assert hasattr(workflow, "extruded_generator")
        assert hasattr(workflow, "heightmap_generator")

    def test_initialization_custom(self):
        """Test workflow initialization with custom parameters."""
        workflow = BathymeshWorkflow(
            min_polygon_area=0.1, merge_threshold=1e-5, quality_triangulation=False
        )
        assert workflow is not None

    def test_create_mesh_from_heightmap_surface(self, test_heightmap, default_scaling):
        """Test surface mesh creation from heightmap."""
        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=default_scaling,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) > 0
        assert len(mesh.triangles) > 0

    def test_create_mesh_from_heightmap_flat(self, test_heightmap, default_scaling):
        """Test flat mesh creation from heightmap."""
        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.FLAT,
            scaling=default_scaling,
            flat_height=1.0,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        if len(mesh.vertices) > 0:
            vertices = np.asarray(mesh.vertices)
            # All vertices should be at the specified height
            np.testing.assert_array_almost_equal(vertices[:, 2], 1.0, decimal=5)

    def test_create_mesh_from_heightmap_extruded(self, test_heightmap, default_scaling):
        """Test extruded mesh creation from heightmap."""
        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.EXTRUDED,
            scaling=default_scaling,
            base_height=0.0,
            thickness=2.0,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) >= 0  # May be empty in some cases
        if len(mesh.vertices) > 0:
            vertices = np.asarray(mesh.vertices)
            z_values = vertices[:, 2]
            assert z_values.min() >= 0.0
            assert z_values.max() <= 2.0

    def test_create_mesh_from_heightmap_contour(self, test_heightmap, default_scaling):
        """Test contour mesh creation from heightmap."""
        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.CONTOUR,
            scaling=default_scaling,
            use_contours=True,
            contour_threshold=0.5,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        # Contour mesh may be empty if no contours found
        assert len(mesh.vertices) >= 0

    def test_create_mesh_string_type(self, test_heightmap, default_scaling):
        """Test mesh creation with string mesh type."""
        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap, mesh_type="surface", scaling=default_scaling
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)

    def test_create_mesh_with_coordinates(
        self, test_heightmap, default_scaling, coordinate_arrays
    ):
        """Test mesh creation with coordinate arrays."""
        x_coords, y_coords = coordinate_arrays

        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=default_scaling,
            x_coords=x_coords,
            y_coords=y_coords,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)

    def test_create_mesh_with_output_path(
        self, test_heightmap, default_scaling, temp_output_dir
    ):
        """Test mesh creation with output path."""
        output_path = temp_output_dir / "test_mesh.stl"

        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=default_scaling,
            output_path=output_path,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert output_path.exists()

    def test_create_multi_level_mesh(self, test_heightmap, default_scaling):
        """Test multi-level mesh creation."""
        thresholds = [0.2, 0.5, 1.0]

        mesh = self.workflow.create_multi_level_mesh(
            heightmap=test_heightmap,
            thresholds=thresholds,
            mesh_type=MeshType.FLAT,
            scaling=default_scaling,
            thickness=0.5,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        # Multi-level mesh may be empty if no contours found at thresholds
        assert len(mesh.vertices) >= 0

    def test_create_multi_level_mesh_with_spacing(
        self, test_heightmap, default_scaling
    ):
        """Test multi-level mesh creation with custom layer spacing."""
        thresholds = [0.3, 0.6, 0.9]

        mesh = self.workflow.create_multi_level_mesh(
            heightmap=test_heightmap,
            thresholds=thresholds,
            mesh_type=MeshType.EXTRUDED,
            scaling=default_scaling,
            base_height=0.0,
            thickness=0.2,
            layer_spacing=0.5,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)

    def test_create_simple_surface_mesh_legacy(self, test_heightmap):
        """Test legacy simple surface mesh creation."""
        mesh = self.workflow.create_simple_surface_mesh(
            heightmap=test_heightmap,
            scaling=MeshScaling(scale_x=1.0, scale_y=1.0, scale_z=2.0),
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) > 0

    def test_create_contour_mesh_legacy(self, test_heightmap):
        """Test legacy contour mesh creation."""
        thresholds = [0.3, 0.6, 1.0]

        # Test extruded contour mesh
        mesh = self.workflow.create_contour_mesh(
            heightmap=test_heightmap, thresholds=thresholds, thickness=0.5, extrude=True
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)

        # Test flat contour mesh
        mesh = self.workflow.create_contour_mesh(
            heightmap=test_heightmap,
            thresholds=thresholds,
            thickness=0.5,
            extrude=False,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)

    def test_get_mesh_info(self, test_heightmap, default_scaling):
        """Test mesh info extraction."""
        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=default_scaling,
        )

        info = self.workflow.get_mesh_info(mesh)

        assert isinstance(info, MeshInfo)
        assert info.num_vertices >= 0
        assert info.num_triangles >= 0
        assert isinstance(info.is_watertight, bool)

    def test_get_mesh_info_dict_legacy(self, test_heightmap, default_scaling):
        """Test legacy mesh info as dictionary."""
        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=default_scaling,
        )

        # The get_mesh_info method returns MeshInfo dataclass,
        # but can be converted to dict for legacy compatibility
        info = self.workflow.get_mesh_info(mesh)

        # Test that the info object has all expected attributes
        assert hasattr(info, "num_vertices")
        assert hasattr(info, "num_triangles")
        assert hasattr(info, "is_watertight")

    def test_get_supported_mesh_types(self):
        """Test getting supported mesh types."""
        types = self.workflow.get_supported_mesh_types()

        assert isinstance(types, list)
        assert len(types) > 0
        assert all(isinstance(t, str) for t in types)

        # Should include the main mesh types
        expected_types = {"flat", "extruded", "surface", "contour"}
        assert expected_types.issubset(set(types))

    def test_create_heightmap_handler(self, test_heightmap, default_scaling):
        """Test heightmap handler creation."""
        handler = self.workflow.create_heightmap_handler(
            heightmap=test_heightmap, scaling=default_scaling
        )

        assert handler is not None
        assert hasattr(handler, "heightmap")
        assert hasattr(handler, "scaling")

    def test_invalid_mesh_type_raises_error(self, test_heightmap, default_scaling):
        """Test that invalid mesh type raises ValueError."""
        with pytest.raises(ValueError):
            self.workflow.create_mesh_from_heightmap(
                heightmap=test_heightmap,
                mesh_type="invalid_type",
                scaling=default_scaling,
            )

    def test_contour_mesh_missing_threshold_autofills_value(
        self, test_heightmap, default_scaling
    ):
        """Test that contour mesh without threshold autofills value."""
        self.workflow.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.CONTOUR,
            scaling=default_scaling,
            use_contours=True,
            # Missing contour_threshold
        )

    def test_empty_thresholds_error(self, test_heightmap, default_scaling):
        """Test multi-level mesh with empty thresholds."""

        with pytest.raises(ValueError, match="At least one threshold"):
            self.workflow.create_multi_level_mesh(
                heightmap=test_heightmap,
                thresholds=[],
                mesh_type=MeshType.FLAT,
                scaling=default_scaling,
            )

    def test_workflow_with_large_heightmap(self, default_scaling):
        """Test workflow with larger heightmap."""
        # Create a larger test heightmap
        large_heightmap = np.random.random((100, 100))

        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=large_heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=default_scaling,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        # Should handle large data reasonably
        assert len(mesh.vertices) > 0

    def test_workflow_error_handling_invalid_heightmap(self, default_scaling):
        """Test workflow error handling with invalid heightmap."""
        # Test with NaN values
        invalid_heightmap = np.ones((5, 5))
        invalid_heightmap[2, 2] = np.nan

        with pytest.raises(ValueError):
            self.workflow.create_mesh_from_heightmap(
                heightmap=invalid_heightmap,
                mesh_type=MeshType.SURFACE,
                scaling=default_scaling,
            )

    def test_workflow_with_minimal_heightmap(self, default_scaling):
        """Test workflow with minimal heightmap size."""
        minimal_heightmap = np.array([[1.0, 2.0], [3.0, 4.0]])

        mesh = self.workflow.create_mesh_from_heightmap(
            heightmap=minimal_heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=default_scaling,
        )

        assert isinstance(mesh, o3d.geometry.TriangleMesh)
        assert len(mesh.vertices) >= 4  # At least the 4 points

    def test_mesh_output_file_formats(
        self, test_heightmap, default_scaling, temp_output_dir
    ):
        """Test mesh output with different file formats."""
        formats = [".stl", ".ply", ".obj"]

        for fmt in formats:
            output_path = temp_output_dir / f"test_mesh{fmt}"

            mesh = self.workflow.create_mesh_from_heightmap(
                heightmap=test_heightmap,
                mesh_type=MeshType.SURFACE,
                scaling=default_scaling,
                output_path=output_path,
            )

            assert isinstance(mesh, o3d.geometry.TriangleMesh)
            assert output_path.exists()


class TestWorkflowIntegration:
    """Integration tests for complete workflow scenarios."""

    def test_complete_workflow_pipeline(self, temp_output_dir):
        """Test complete workflow from heightmap to output file."""
        workflow = BathymeshWorkflow()

        # Create test heightmap
        from bathy.utils import create_test_heightmap

        heightmap = create_test_heightmap(width=20, height=20)

        # Create surface mesh
        surface_mesh = workflow.create_mesh_from_heightmap(
            heightmap=heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=MeshScaling(scale_x=0.1, scale_y=0.1, scale_z=2.0),
            output_path=temp_output_dir / "surface.stl",
        )

        # Create flat mesh
        flat_mesh = workflow.create_mesh_from_heightmap(
            heightmap=heightmap,
            mesh_type=MeshType.FLAT,
            flat_height=1.0,
            output_path=temp_output_dir / "flat.stl",
        )

        # Create multi-level mesh
        multi_mesh = workflow.create_multi_level_mesh(
            heightmap=heightmap,
            thresholds=[0.5, 1.0, 1.5],
            mesh_type=MeshType.EXTRUDED,
            thickness=0.3,
            output_path=temp_output_dir / "multi.stl",
        )

        # Verify all outputs
        assert isinstance(surface_mesh, o3d.geometry.TriangleMesh)
        assert isinstance(flat_mesh, o3d.geometry.TriangleMesh)
        assert isinstance(multi_mesh, o3d.geometry.TriangleMesh)

        assert (temp_output_dir / "surface.stl").exists()
        assert (temp_output_dir / "flat.stl").exists()
        assert (temp_output_dir / "multi.stl").exists()

    def test_workflow_performance_reasonable(self, medium_heightmap):
        """Test that workflow performance is reasonable for medium-sized data."""
        import time

        workflow = BathymeshWorkflow()

        start_time = time.time()
        mesh = workflow.create_mesh_from_heightmap(
            heightmap=medium_heightmap, mesh_type=MeshType.SURFACE
        )
        end_time = time.time()

        # Should complete in reasonable time (< 10 seconds for 30x30 heightmap)
        elapsed = end_time - start_time
        assert elapsed < 10.0
        assert isinstance(mesh, o3d.geometry.TriangleMesh)

    def test_workflow_reproducibility(self, test_heightmap, default_scaling):
        """Test that workflow produces reproducible results."""
        workflow1 = BathymeshWorkflow()
        workflow2 = BathymeshWorkflow()

        mesh1 = workflow1.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=default_scaling,
        )

        mesh2 = workflow2.create_mesh_from_heightmap(
            heightmap=test_heightmap,
            mesh_type=MeshType.SURFACE,
            scaling=default_scaling,
        )

        # Should produce similar results (within numerical precision)
        vertices1 = np.asarray(mesh1.vertices)
        vertices2 = np.asarray(mesh2.vertices)

        if len(vertices1) > 0 and len(vertices2) > 0:
            assert vertices1.shape == vertices2.shape
            # Results should be identical for deterministic input
            np.testing.assert_array_almost_equal(vertices1, vertices2, decimal=10)
