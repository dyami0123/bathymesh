import numpy as np
import open3d as o3d
from shapely.geometry import Polygon
from skimage import measure
import triangle as tr

def triangulate_with_triangle(poly: Polygon):
    """
    Triangulate a polygon using the triangle library.
    
    Args:
        poly: Shapely Polygon object
        
    Returns:
        tuple: (vertices, triangles) where vertices is array of 2D coordinates
               and triangles is array of triangle indices
    """
    # Get exterior + holes
    exterior = np.array(poly.exterior.coords[:-1])
    holes = [np.array(ring.coords[:-1]) for ring in poly.interiors]
    # Build vertices & segments
    verts = []
    segments = []
    hole_points = []
    idx = 0
    
    # Exterior ring
    for i, v in enumerate(exterior):
        verts.append((v[0], v[1]))
        segments.append((idx + i, idx + ((i + 1) % len(exterior))))
    idx += len(exterior)
    
    # Holes
    for hole in holes:
        # pick a point inside the hole as hole marker
        centroid = Polygon(hole).centroid.coords[0]
        hole_points.append(centroid)
        for i, v in enumerate(hole):
            verts.append((v[0], v[1]))
            segments.append((idx + i, idx + ((i + 1) % len(hole))))
        idx += len(hole)
    
    data = {
        'vertices': np.array(verts),
        'segments': np.array(segments),
    }
    if len(hole_points) > 0:
        data['holes'] = np.array(hole_points)
    # 'p' = use PSLG, 'q' = quality, other flags as you need
    tri = tr.triangulate(data, 'p')  
    # tri['triangles'] gives indices into tri['vertices']
    return tri['vertices'], tri['triangles']

def extract_polygons_from_heightmap(heightmap, threshold):
    """
    Extract closed polygons (contours) from a 2D heightmap at a given threshold.
    """
    contours = measure.find_contours(heightmap, threshold)
    polygons = []

    for contour in contours:
        # Flip axis to get (x, y) instead of (row, col)
        coords = np.flip(contour, axis=1)
        if len(coords) >= 3:
            poly = Polygon(coords)
            if poly.is_valid and poly.area > 1e-2:
                polygons.append(poly)

    return polygons

def polygon_to_extruded_mesh(polygon: Polygon, height: float, thickness: float, extrude: bool = True):
    """
    Convert a polygon to a 3D mesh, optionally with extrusion.
    
    Args:
        polygon: Shapely Polygon object
        height: Base height (z-coordinate) for the polygon
        thickness: Thickness of extrusion (ignored if extrude=False)
        extrude: If True, creates extruded 3D mesh; if False, creates flat polygon at height
    
    Returns:
        open3d.geometry.TriangleMesh
    """
    # Use triangle library for triangulation
    vertices_2d, triangles = triangulate_with_triangle(polygon)
    
    print(f"Debug: vertices_2d.shape = {vertices_2d.shape}, triangles.shape = {triangles.shape}")
    print(f"Debug: triangles min/max = {triangles.min()}/{triangles.max()}")

    if not extrude:
        # Create only a flat polygon at the specified height
        vertices_3d = np.column_stack((vertices_2d, np.full(len(vertices_2d), height)))
        faces = triangles
        
        # Build mesh
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(vertices_3d)
        mesh.triangles = o3d.utility.Vector3iVector(faces)
        mesh.compute_vertex_normals()
        return mesh
    
    # Create 3D vertices for extruded mesh
    bottom_z = height
    top_z = height + thickness
    bottom_vertices = np.column_stack((vertices_2d, np.full(len(vertices_2d), bottom_z)))
    top_vertices = np.column_stack((vertices_2d, np.full(len(vertices_2d), top_z)))

    all_vertices = np.vstack((bottom_vertices, top_vertices))
    n = len(bottom_vertices)
    
    print(f"Debug: all_vertices.shape = {all_vertices.shape}, n = {n}")

    # Faces
    bottom_faces = triangles
    top_faces = triangles[:, ::-1] + n  # Reverse winding and offset indices
    
    print(f"Debug: bottom_faces.shape = {bottom_faces.shape}")
    print(f"Debug: top_faces.shape = {top_faces.shape}")
    print(f"Debug: top_faces min/max = {top_faces.min()}/{top_faces.max()}")

    # Build side faces more carefully
    side_faces = []
    
    # Map triangulated vertices back to polygon boundary
    # This is the problematic part - we need to identify boundary edges
    
    # For now, let's try a simpler approach: use the exterior boundary only
    exterior_coords = np.array(polygon.exterior.coords[:-1])  # Remove duplicate last point
    print(f"Debug: exterior_coords.shape = {exterior_coords.shape}")
    
    # Find vertices that correspond to boundary points
    boundary_indices = []
    for ext_coord in exterior_coords:
        # Find closest vertex in triangulated vertices
        distances = np.sum((vertices_2d - ext_coord)**2, axis=1)
        closest_idx = np.argmin(distances)
        boundary_indices.append(closest_idx)
    
    print(f"Debug: boundary_indices = {boundary_indices}")
    
    # Create side faces from boundary
    for i in range(len(boundary_indices)):
        curr_idx = boundary_indices[i]
        next_idx = boundary_indices[(i + 1) % len(boundary_indices)]
        
        # Validate indices
        if curr_idx >= n or next_idx >= n:
            print(f"Warning: Invalid boundary index {curr_idx} or {next_idx}, skipping")
            continue
            
        # Two triangles for each edge
        side_faces.extend([
            [curr_idx, next_idx, next_idx + n],
            [curr_idx, next_idx + n, curr_idx + n]
        ])
    
    if len(side_faces) == 0:
        print("Warning: No side faces created, returning non-extruded mesh")
        return polygon_to_extruded_mesh(polygon, height, thickness, extrude=False)
    
    side_faces = np.array(side_faces)
    print(f"Debug: side_faces.shape = {side_faces.shape}")
    print(f"Debug: side_faces min/max = {side_faces.min()}/{side_faces.max()}")
    
    # Validate all face indices
    max_vertex_idx = len(all_vertices) - 1
    all_face_arrays = [bottom_faces, top_faces, side_faces]
    
    for i, face_array in enumerate(all_face_arrays):
        face_names = ["bottom", "top", "side"]
        if face_array.max() > max_vertex_idx:
            print(f"Error: {face_names[i]} faces have invalid indices. Max index: {face_array.max()}, Max valid: {max_vertex_idx}")
            return o3d.geometry.TriangleMesh()  # Return empty mesh on error

    faces = np.vstack((bottom_faces, top_faces, side_faces))
    print(f"Debug: Final faces.shape = {faces.shape}")

    # Build mesh
    try:
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(all_vertices)
        mesh.triangles = o3d.utility.Vector3iVector(faces)
        mesh.compute_vertex_normals()
        return mesh
    except Exception as e:
        print(f"Error creating mesh: {e}")
        return o3d.geometry.TriangleMesh()  # Return empty mesh on error

def simple_heightmap_mesh(heightmap, scale_x=1.0, scale_y=1.0, scale_z=1.0):
    """
    Create a simple surface mesh directly from a 2D heightmap.
    This is a simpler alternative for proof of concept testing.
    
    Args:
        heightmap: 2D numpy array representing height values
        scale_x, scale_y, scale_z: scaling factors for each dimension
    
    Returns:
        open3d.geometry.TriangleMesh
    """
    height, width = heightmap.shape
    
    # Create vertices
    vertices = []
    for i in range(height):
        for j in range(width):
            x = j * scale_x
            y = i * scale_y
            z = heightmap[i, j] * scale_z
            vertices.append([x, y, z])
    
    vertices = np.array(vertices)
    
    # Create triangular faces
    faces = []
    for i in range(height - 1):
        for j in range(width - 1):
            # Two triangles per grid cell
            v1 = i * width + j
            v2 = i * width + (j + 1)
            v3 = (i + 1) * width + j
            v4 = (i + 1) * width + (j + 1)
            
            # First triangle
            faces.append([v1, v2, v3])
            # Second triangle
            faces.append([v2, v4, v3])
    
    faces = np.array(faces)
    
    # Create Open3D mesh
    mesh = o3d.geometry.TriangleMesh()
    mesh.vertices = o3d.utility.Vector3dVector(vertices)
    mesh.triangles = o3d.utility.Vector3iVector(faces)
    mesh.compute_vertex_normals()
    
    return mesh

def build_extruded_mesh_from_heightmap(heightmap, thresholds, thickness=1.0, extrude=True):
    """
    Build a mesh from heightmap contours at specified thresholds.
    
    Args:
        heightmap: 2D numpy array of height values
        thresholds: List of height values to extract contours at
        thickness: Thickness for extrusion (ignored if extrude=False)
        extrude: If True, creates extruded meshes; if False, creates flat polygons
    
    Returns:
        open3d.geometry.TriangleMesh
    """
    all_meshes = []
    for level_idx, level in enumerate(thresholds):
        print(f"Processing threshold level {level_idx + 1}/{len(thresholds)}: {level}")
        polygons = extract_polygons_from_heightmap(heightmap, level)
        print(f"Found {len(polygons)} polygons at level {level}")
        
        for poly_idx, poly in enumerate(polygons):
            print(f"  Processing polygon {poly_idx + 1}/{len(polygons)}")
            print(f"  Polygon area: {poly.area}, bounds: {poly.bounds}")
            try:
                mesh = polygon_to_extruded_mesh(poly, height=level * thickness, thickness=thickness, extrude=extrude)
                if len(mesh.vertices) > 0:  # Only add non-empty meshes
                    all_meshes.append(mesh)
                    print(f"  Successfully created mesh with {len(mesh.vertices)} vertices")
                else:
                    print(f"  Skipping empty mesh")
            except Exception as e:
                print(f"  Error processing polygon {poly_idx}: {e}")
                import traceback
                traceback.print_exc()
                continue

    if not all_meshes:
        # Return empty mesh if no polygons found
        print("No valid meshes created, returning empty mesh")
        return o3d.geometry.TriangleMesh()

    print(f"Combining {len(all_meshes)} meshes...")
    # Combine all meshes into one
    combined = all_meshes[0]
    for i, m in enumerate(all_meshes[1:], 1):
        print(f"  Combining mesh {i + 1}/{len(all_meshes)}")
        try:
            combined += m
        except Exception as e:
            print(f"  Error combining mesh {i}: {e}")
            continue

    print("Merging close vertices...")
    combined.merge_close_vertices(1e-6)
    combined.compute_vertex_normals()
    return combined

if __name__ == "__main__":
    # Create a more interesting test heightmap
    x = np.linspace(-50, 50, 50)
    y = np.linspace(-50, 50, 50)
    X, Y = np.meshgrid(x, y)
    
    # Create a heightmap with some interesting features
    heightmap = (
        3 * np.exp(-(X**2 + Y**2)/40) +  # Central peak
        2 * np.exp(-((X-2)**2 + (Y-2)**2)/20) +  # Secondary peak
        1 * np.exp(-((X+2)**2 + (Y+1)**2)/30) +  # Another feature
        0.5 * np.sin(X) * np.cos(Y) +  # Some noise
        np.random.normal(0, 0.1, X.shape)  # Random noise
    )
    
    # Scale the heightmap by 10
    # heightmap = heightmap * 10
    
    print("Testing simple heightmap mesh...")
    # Test the simple heightmap mesh
    simple_mesh = simple_heightmap_mesh(heightmap, scale_x=1, scale_y=1, scale_z=10.0)
    print(f"Simple mesh created with {len(simple_mesh.vertices)} vertices and {len(simple_mesh.triangles)} triangles")
    
    # Visualize the simple mesh
    print("Visualizing simple heightmap mesh...")
    
    # Save the simple mesh to STL
    o3d.io.write_triangle_mesh("simple_heightmap_mesh.stl", simple_mesh)
    print("Saved simple heightmap mesh to simple_heightmap_mesh.stl")
    
    # o3d.visualization.draw_geometries([simple_mesh], window_name="Simple Heightmap Mesh")
    
    # Optionally test the polygon-based mesh (comment out if having issues)
    test_polygon_mesh = True  # Set to False if you want to skip this test
    
    if test_polygon_mesh:
        print("Testing polygon-based mesh (flat polygons)...")
        thresholds = [1, 2, 3, 4]  # Example thresholds
        
        try:
            # Test flat polygons first (no extrusion)
            flat_mesh = build_extruded_mesh_from_heightmap(heightmap, thresholds, thickness=1, extrude=False)
            print(f"Flat polygon mesh created with {len(flat_mesh.vertices)} vertices and {len(flat_mesh.triangles)} triangles")
            
            # Save and visualize the flat mesh
            o3d.io.write_triangle_mesh("flat_polygon_mesh.stl", flat_mesh)
            print("Saved flat polygon mesh to flat_polygon_mesh.stl")
            # o3d.visualization.draw_geometries([flat_mesh], window_name="Flat Polygon Mesh")
            
        except Exception as e:
            print(f"Error creating flat polygon mesh: {e}")
            import traceback
            traceback.print_exc()
    
    # Test extruded version
    test_extruded = True  # Set to True when you want to test the extruded version
    
    if test_extruded:
        print("Testing extruded mesh...")
        thresholds = [1, 2, 3, 4]  # Example thresholds
        thickness = 0.2  # Extrusion thickness
        
        try:
            extruded_mesh = build_extruded_mesh_from_heightmap(heightmap, thresholds, thickness, extrude=True)
            print(f"Extruded mesh created with {len(extruded_mesh.vertices)} vertices and {len(extruded_mesh.triangles)} triangles")
            # o3d.visualization.draw_geometries([extruded_mesh], window_name="Extruded Heightmap Mesh")
            
            o3d.io.write_triangle_mesh("extruded_heightmap_mesh.stl", extruded_mesh)
            print("Saved extruded mesh to extruded_heightmap_mesh.stl")
            
        except Exception as e:
            print(f"Error creating extruded mesh: {e}")
            print("Falling back to simple mesh visualization")
            
        