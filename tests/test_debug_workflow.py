"""Tests for debug workflow."""

import pytest
import numpy as np
from pathlib import Path
import tempfile
import shutil

from bathymesh.workflows import (
    DebugWorkflow,
    DebugWorkflowConfig,
    HeightmapGenerationConfig,
    DebugVisualizationConfig,
    DebugWorkflowResult
)
from bathymesh.workflows.multi_level_mesh_generation_workflow import MultiLevelMeshConfig
from bathymesh.workflows.simple_mesh_generation_workflow import SimpleMeshConfig
from bathymesh.data_structures import MeshType, MeshScaling


class TestHeightmapGenerationConfig:
    """Tests for heightmap generation configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = HeightmapGenerationConfig()
        
        assert config.size == 300
        assert config.x_range == (-1.0, 1.0)
        assert config.y_range == (-1.0, 1.0)
        assert config.central_peak == 0.8
        assert config.secondary_peak == 1.8
        assert config.wave_pattern == 1.8
        assert config.noise_level == 0.0
        assert config.add_zero_border is True
        assert config.border_width == 2
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = HeightmapGenerationConfig(
            size=100,
            central_peak=2.0,
            noise_level=0.5,
            add_zero_border=False
        )
        
        assert config.size == 100
        assert config.central_peak == 2.0
        assert config.noise_level == 0.5
        assert config.add_zero_border is False


class TestDebugVisualizationConfig:
    """Tests for debug visualization configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = DebugVisualizationConfig()
        
        assert config.enabled is True
        assert config.clear_before_run is True
        assert config.save_heightmap_image is True
        assert config.show_contour_lines is True
        assert config.colormap == "terrain"
        assert config.open_in_vscode is False
        assert config.open_in_slicer is False
    
    def test_custom_config(self):
        """Test custom configuration."""
        config = DebugVisualizationConfig(
            enabled=False,
            colormap="viridis",
            open_in_slicer=True
        )
        
        assert config.enabled is False
        assert config.colormap == "viridis"
        assert config.open_in_slicer is True


class TestDebugWorkflow:
    """Tests for DebugWorkflow class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_init_default(self):
        """Test workflow initialization with defaults."""
        workflow = DebugWorkflow()
        
        assert workflow.config is not None
        assert isinstance(workflow.config, DebugWorkflowConfig)
    
    def test_init_with_config(self):
        """Test workflow initialization with config object."""
        config = DebugWorkflowConfig(verbose=False)
        workflow = DebugWorkflow(config=config)
        
        assert workflow.config is config
        assert workflow.config.verbose is False
    
    def test_init_with_kwargs(self):
        """Test workflow initialization with kwargs."""
        workflow = DebugWorkflow(verbose=False)
        
        assert workflow.config.verbose is False
    
    def test_init_reject_both(self):
        """Test that providing both config and kwargs raises error."""
        config = DebugWorkflowConfig()
        
        with pytest.raises(ValueError, match="Cannot provide both"):
            DebugWorkflow(config=config, verbose=False)
    
    def test_heightmap_generation_default(self, temp_dir):
        """Test default heightmap generation."""
        config = DebugWorkflowConfig(
            heightmap_config=HeightmapGenerationConfig(size=50),
            mesh_config=SimpleMeshConfig(mesh_type=MeshType.SURFACE),
            visualization_config=DebugVisualizationConfig(
                enabled=False  # Disable viz for faster tests
            ),
            verbose=False
        )
        
        workflow = DebugWorkflow(config)
        result = workflow.execute()
        
        assert isinstance(result, DebugWorkflowResult)
        assert result.heightmap.shape == (54, 54)  # 50 + 2*2 border
        assert 'min' in result.heightmap_stats
        assert 'max' in result.heightmap_stats
    
    def test_heightmap_generation_no_border(self, temp_dir):
        """Test heightmap generation without border."""
        config = DebugWorkflowConfig(
            heightmap_config=HeightmapGenerationConfig(
                size=50,
                add_zero_border=False
            ),
            mesh_config=SimpleMeshConfig(mesh_type=MeshType.SURFACE),
            visualization_config=DebugVisualizationConfig(enabled=False),
            verbose=False
        )
        
        workflow = DebugWorkflow(config)
        result = workflow.execute()
        
        assert result.heightmap.shape == (50, 50)
    
    def test_heightmap_generation_with_noise(self, temp_dir):
        """Test heightmap generation with noise."""
        config = DebugWorkflowConfig(
            heightmap_config=HeightmapGenerationConfig(
                size=50,
                noise_level=0.5,
                add_zero_border=False
            ),
            mesh_config=SimpleMeshConfig(mesh_type=MeshType.SURFACE),
            visualization_config=DebugVisualizationConfig(enabled=False),
            verbose=False
        )
        
        workflow = DebugWorkflow(config)
        result = workflow.execute()
        
        # With noise, std should be non-zero
        assert result.heightmap_stats['std'] > 0
    
    def test_custom_heightmap_generator(self, temp_dir):
        """Test using custom heightmap generator."""
        def custom_generator():
            return np.ones((100, 100))
        
        config = DebugWorkflowConfig(
            custom_heightmap_generator=custom_generator,
            mesh_config=SimpleMeshConfig(mesh_type=MeshType.SURFACE),
            visualization_config=DebugVisualizationConfig(enabled=False),
            verbose=False
        )
        
        workflow = DebugWorkflow(config)
        result = workflow.execute()
        
        assert result.heightmap.shape == (100, 100)
        assert np.all(result.heightmap == 1.0)
    
    def test_simple_mesh_generation(self, temp_dir):
        """Test simple mesh generation."""
        config = DebugWorkflowConfig(
            heightmap_config=HeightmapGenerationConfig(size=30),
            mesh_config=SimpleMeshConfig(
                mesh_type=MeshType.SURFACE,
                save_output=True,
                output_path=temp_dir / "test_mesh.stl"
            ),
            visualization_config=DebugVisualizationConfig(enabled=False),
            verbose=False
        )
        
        workflow = DebugWorkflow(config)
        result = workflow.execute()
        
        assert len(result.mesh_result.mesh.vertices) > 0
        assert (temp_dir / "test_mesh.stl").exists()
    
    def test_multi_level_mesh_generation(self, temp_dir):
        """Test multi-level mesh generation."""
        config = DebugWorkflowConfig(
            heightmap_config=HeightmapGenerationConfig(size=30),
            mesh_config=MultiLevelMeshConfig(
                thresholds=[0.0, 0.5, 1.0],
                mesh_type=MeshType.EXTRUDED,
                thickness=0.1,
                save_output=True,
                output_path=temp_dir / "test_multilevel.stl"
            ),
            visualization_config=DebugVisualizationConfig(enabled=False),
            verbose=False
        )
        
        workflow = DebugWorkflow(config)
        result = workflow.execute()
        
        assert len(result.mesh_result.mesh.vertices) > 0
        assert result.mesh_result.num_levels >= 0
        assert (temp_dir / "test_multilevel.stl").exists()
    
    def test_visualization_enabled(self, temp_dir):
        """Test with visualization enabled."""
        viz_dir = temp_dir / "viz"
        
        config = DebugWorkflowConfig(
            heightmap_config=HeightmapGenerationConfig(size=30),
            mesh_config=SimpleMeshConfig(mesh_type=MeshType.SURFACE),
            visualization_config=DebugVisualizationConfig(
                enabled=True,
                output_directory=viz_dir,
                save_heightmap_image=True,
                show_contour_lines=False
            ),
            verbose=False
        )
        
        workflow = DebugWorkflow(config)
        result = workflow.execute()
        
        assert len(result.visualization_outputs) > 0
        assert viz_dir.exists()
        assert (viz_dir / "generated_heightmap.png").exists()
    
    def test_visualization_with_contours(self, temp_dir):
        """Test visualization with contour lines."""
        viz_dir = temp_dir / "viz"
        
        config = DebugWorkflowConfig(
            heightmap_config=HeightmapGenerationConfig(size=30),
            mesh_config=MultiLevelMeshConfig(
                thresholds=[0.0, 0.5, 1.0],
                mesh_type=MeshType.FLAT
            ),
            visualization_config=DebugVisualizationConfig(
                enabled=True,
                output_directory=viz_dir,
                show_contour_lines=True
            ),
            verbose=False
        )
        
        workflow = DebugWorkflow(config)
        result = workflow.execute()
        
        assert len(result.visualization_outputs) > 0
    
    def test_quick_run(self, temp_dir):
        """Test quick_run class method."""
        result = DebugWorkflow.quick_run(
            mesh_type=MeshType.SURFACE,
            size=30,
            output_path=temp_dir / "quick_mesh.stl"
        )
        
        assert isinstance(result, DebugWorkflowResult)
        assert len(result.mesh_result.mesh.vertices) > 0
    
    def test_quick_run_multi_level(self, temp_dir):
        """Test quick_run with multi-level mesh."""
        result = DebugWorkflow.quick_run(
            mesh_type=MeshType.EXTRUDED,
            size=30,
            thresholds=[0.0, 0.5, 1.0],
            thickness=0.1,
            output_path=temp_dir / "quick_multilevel.stl"
        )
        
        assert isinstance(result, DebugWorkflowResult)
        assert len(result.mesh_result.mesh.vertices) > 0
    
    def test_result_str_representation(self, temp_dir):
        """Test result string representation."""
        result = DebugWorkflow.quick_run(
            mesh_type=MeshType.SURFACE,
            size=30
        )
        
        result_str = str(result)
        assert "Debug Workflow Results" in result_str
        assert "Heightmap shape" in result_str
        assert "Heightmap range" in result_str


class TestDebugWorkflowIntegration:
    """Integration tests for complete workflow scenarios."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)
    
    def test_end_to_end_surface_mesh(self, temp_dir):
        """Test complete workflow for surface mesh."""
        output_file = temp_dir / "surface.stl"
        viz_dir = temp_dir / "viz"
        
        config = DebugWorkflowConfig(
            heightmap_config=HeightmapGenerationConfig(
                size=50,
                central_peak=1.0,
                noise_level=0.0
            ),
            mesh_config=SimpleMeshConfig(
                mesh_type=MeshType.SURFACE,
                save_output=True,
                output_path=output_file
            ),
            visualization_config=DebugVisualizationConfig(
                enabled=True,
                output_directory=viz_dir,
                clear_before_run=True
            ),
            verbose=False
        )
        
        workflow = DebugWorkflow(config)
        result = workflow.execute()
        
        # Verify heightmap
        assert result.heightmap is not None
        assert result.heightmap.shape[0] > 0
        
        # Verify mesh
        assert len(result.mesh_result.mesh.vertices) > 0
        assert len(result.mesh_result.mesh.triangles) > 0
        
        # Verify output file
        assert output_file.exists()
        
        # Verify visualizations
        assert len(result.visualization_outputs) > 0
        assert viz_dir.exists()
    
    def test_end_to_end_multi_level(self, temp_dir):
        """Test complete workflow for multi-level mesh."""
        output_file = temp_dir / "multilevel.stl"
        
        result = DebugWorkflow.quick_run(
            mesh_type=MeshType.EXTRUDED,
            size=50,
            thresholds=[0.0, 1.0, 2.0],
            thickness=0.2,
            output_path=output_file,
            scaling=MeshScaling(scale_x=0.5, scale_y=0.5, scale_z=1.0)
        )
        
        # Verify result
        assert result.heightmap is not None
        assert len(result.mesh_result.mesh.vertices) > 0
        assert output_file.exists()
        
        # Verify multi-level specific attributes
        assert hasattr(result.mesh_result, 'num_levels')
        assert result.mesh_result.num_levels >= 0
