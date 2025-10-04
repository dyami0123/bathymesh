# Bathymesh Runner Configuration Examples
# Copy these configurations into run_bathymesh.py to try different mesh types
# Note: This file contains example configurations - not executable code

# Example 1: Simple Surface Mesh
EXAMPLE_SURFACE = {
    "MESH_CONFIG": {
        "type": "MeshType.SURFACE",  # Replace with actual enum in run_bathymesh.py
        "scaling": "MeshScaling(scale_x=0.05, scale_y=0.05, scale_z=2.0)",
        "base_height": 0.0
    },
    "OUTPUT_CONFIG": {
        "filename": "surface_mesh"
    }
}

# Example 2: Extruded Terrain Block
EXAMPLE_EXTRUDED = {
    "MESH_CONFIG": {
        "type": "MeshType.EXTRUDED",
        "scaling": "MeshScaling(scale_x=0.04, scale_y=0.04, scale_z=1.0)",
        "base_height": 0.0,
        "thickness": 2.0,
        "use_contours": False
    },
    "OUTPUT_CONFIG": {
        "filename": "extruded_terrain"
    }
}

# Example 3: Multi-Level Contour Mesh
EXAMPLE_MULTI_LEVEL = {
    "MESH_CONFIG": {
        "type": "MeshType.EXTRUDED",
        "scaling": "MeshScaling(scale_x=0.03, scale_y=0.03, scale_z=1.5)",
        "base_height": 0.0,
        "thickness": 0.5,
        "multi_level": {
            "enabled": True,
            "thresholds": [0.2, 0.5, 0.8, 1.1, 1.4],
            "layer_spacing": 0.6
        }
    },
    "OUTPUT_CONFIG": {
        "filename": "multi_level_terrain"
    }
}

# Example 4: High-Resolution Flat Contour
EXAMPLE_FLAT_CONTOUR = {
    "HEIGHTMAP_CONFIG": {
        "size": 80,
        "features": {
            "central_peak": 1.5,
            "secondary_peak": 0.8,
            "wave_pattern": 0.2,
            "noise_level": 0.02
        }
    },
    "MESH_CONFIG": {
        "type": "MeshType.FLAT",
        "scaling": "MeshScaling(scale_x=0.025, scale_y=0.025, scale_z=1.0)",
        "flat_height": 1.0,
        "use_contours": True,
        "contour_threshold": 0.7
    },
    "OUTPUT_CONFIG": {
        "filename": "flat_contour_high_res"
    }
}

# Example 5: Simple Mountain Range
EXAMPLE_MOUNTAINS = {
    "HEIGHTMAP_CONFIG": {
        "size": 100,
        "x_range": (-5, 5),
        "y_range": (-5, 5),
        "features": {
            "central_peak": 2.0,
            "secondary_peak": 1.2,
            "wave_pattern": 0.1,
            "noise_level": 0.1
        }
    },
    "MESH_CONFIG": {
        "type": "MeshType.SURFACE",
        "scaling": "MeshScaling(scale_x=0.02, scale_y=0.02, scale_z=3.0)",
        "base_height": -0.5
    },
    "OUTPUT_CONFIG": {
        "filename": "mountain_range"
    }
}

# Usage Instructions:
# 1. Copy the desired configuration sections from above
# 2. Replace the corresponding sections in run_bathymesh.py
# 3. Run: uv run scripts/run_bathymesh.py
