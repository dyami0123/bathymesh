#!/usr/bin/env python3
"""Validate generated STL files and compare with original test script output."""

import logging
from pathlib import Path
import open3d as o3d

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_stl_file(filepath: Path) -> dict:
    """Validate an STL file and return mesh information."""
    try:
        mesh = o3d.io.read_triangle_mesh(str(filepath))
        
        if len(mesh.vertices) == 0:
            return {"valid": False, "error": "Empty mesh"}
        
        # Compute mesh properties
        mesh.compute_vertex_normals()
        
        info = {
            "valid": True,
            "vertices": len(mesh.vertices),
            "triangles": len(mesh.triangles),
            "watertight": mesh.is_watertight(),
            "orientable": mesh.is_orientable(),
            "has_vertex_normals": mesh.has_vertex_normals(),
            "has_triangle_normals": mesh.has_triangle_normals(),
        }
        
        # Bounding box
        if len(mesh.vertices) > 0:
            bbox = mesh.get_axis_aligned_bounding_box()
            info["bounding_box"] = {
                "min": bbox.min_bound.tolist(),
                "max": bbox.max_bound.tolist(),
                "extent": bbox.get_extent().tolist(),
            }
        
        return info
        
    except Exception as e:
        return {"valid": False, "error": str(e)}

def main():
    """Validate all generated STL files."""
    logger.info("Validating bathymesh v0.1 generated STL files")
    
    project_root = Path(__file__).parent.parent
    
    # Files to validate
    stl_files = [
        "simple_heightmap_mesh_v0.1.stl",
        "flat_contour_mesh_v0.1.stl", 
        "extruded_contour_mesh_v0.1.stl",
        # Also check original test script outputs for comparison
        "simple_heightmap_mesh.stl",
        "flat_polygon_mesh.stl",
        "extruded_heightmap_mesh.stl",
    ]
    
    results = {}
    
    for filename in stl_files:
        filepath = project_root / filename
        if filepath.exists():
            logger.info(f"Validating {filename}...")
            results[filename] = validate_stl_file(filepath)
        else:
            logger.warning(f"File not found: {filename}")
            results[filename] = {"valid": False, "error": "File not found"}
    
    # Print results
    logger.info("\n" + "="*80)
    logger.info("VALIDATION RESULTS")
    logger.info("="*80)
    
    for filename, info in results.items():
        logger.info(f"\n{filename}:")
        if info["valid"]:
            logger.info(f"  ✅ Valid mesh")
            logger.info(f"  📊 {info['vertices']} vertices, {info['triangles']} triangles")
            logger.info(f"  🔒 Watertight: {info['watertight']}")
            logger.info(f"  🧭 Orientable: {info['orientable']}")
            if "bounding_box" in info:
                extent = info["bounding_box"]["extent"]
                logger.info(f"  📏 Size: {extent[0]:.1f} × {extent[1]:.1f} × {extent[2]:.1f}")
        else:
            logger.error(f"  ❌ Invalid: {info['error']}")
    
    # Summary comparison
    logger.info("\n" + "="*80)
    logger.info("LIBRARY vs ORIGINAL COMPARISON")
    logger.info("="*80)
    
    comparisons = [
        ("simple_heightmap_mesh_v0.1.stl", "simple_heightmap_mesh.stl"),
        ("flat_contour_mesh_v0.1.stl", "flat_polygon_mesh.stl"),
        ("extruded_contour_mesh_v0.1.stl", "extruded_heightmap_mesh.stl"),
    ]
    
    for new_file, old_file in comparisons:
        if new_file in results and old_file in results:
            new_info = results[new_file]
            old_info = results[old_file]
            
            if new_info["valid"] and old_info["valid"]:
                logger.info(f"\n{new_file.replace('_v0.1', '')} comparison:")
                logger.info(f"  Library v0.1: {new_info['vertices']} vertices, {new_info['triangles']} triangles")
                logger.info(f"  Original:     {old_info['vertices']} vertices, {old_info['triangles']} triangles")
                
                # Check if similar (within reasonable range)
                vertex_ratio = new_info['vertices'] / old_info['vertices'] if old_info['vertices'] > 0 else float('inf')
                triangle_ratio = new_info['triangles'] / old_info['triangles'] if old_info['triangles'] > 0 else float('inf')
                
                if 0.8 <= vertex_ratio <= 1.2 and 0.8 <= triangle_ratio <= 1.2:
                    logger.info(f"  ✅ Similar mesh complexity")
                else:
                    logger.info(f"  ⚠️  Different mesh complexity (ratios: {vertex_ratio:.2f}v, {triangle_ratio:.2f}t)")
            else:
                logger.warning(f"\n{new_file.replace('_v0.1', '')} comparison: Cannot compare (invalid meshes)")

if __name__ == "__main__":
    main()
