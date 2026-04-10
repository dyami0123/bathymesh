# Bathymesh Architecture

## Overview

**Bathymesh**: Python library for converting maps/images/grids → 3D printing meshes.

```
Image/NetCDF → Heightmap (NumPy) → Contours → Triangulation → 3D Mesh → STL/PLY/OBJ
```

---

## File Structure

```
bathymesh/
├── main.py                    # Entry point (stub)
├── pyproject.toml             # Config & deps
├── python/bathy/              # Main package
│   ├── config.py              # Configuration dataclasses
│   ├── data_model.py          # Core data structures
│   ├── contour_extractor.py   # Contour extraction
│   ├── triangulator.py        # Polygon triangulation
│   ├── mesh_generator.py      # Main orchestrator
│   ├── mesh_combiner.py       # Mesh combination
│   ├── mesh_post_processor.py # Cleanup & optimization
│   ├── image_processing/
│   │   ├── image_processor.py # Image → heightmap
│   │   └── color_mapper.py    # Color → value mapping
│   ├── workflows/
│   │   ├── generate_mesh.py   # Mesh generation workflow
│   │   └── process_image.py   # Image processing workflow
│   └── viz/                   # Visualization
├── scripts/                   # Example scripts
└── tests/                     # Test suite
```

---

## Class Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CONFIGURATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────┐                                                │
│  │  MeshGenerationConfig   │ ◄── Top-level config                          │
│  ├─────────────────────────┤                                                │
│  │ stateless: bool         │                                                │
│  │ heightmap_processing ───┼──┐                                             │
│  │ contour_extraction ─────┼──┼──┐                                          │
│  │ triangulation ──────────┼──┼──┼──┐                                       │
│  │ post_processing ────────┼──┼──┼──┼──┐                                    │
│  │ mesh_combination ───────┼──┼──┼──┼──┼──┐                                 │
│  └─────────────────────────┘  │  │  │  │  │                                 │
│                               ▼  │  │  │  │                                 │
│  ┌───────────────────────────────┐  │  │  │                                 │
│  │ HeighmapProcessingConfig      │  │  │  │                                 │
│  ├───────────────────────────────┤  │  │  │                                 │
│  │ exterior_buffer_width: int    │  │  │  │                                 │
│  │ exterior_buffer_value: float  │  │  │  │                                 │
│  │ data_offset: float            │  │  │  │                                 │
│  │ mesh_units: MeshUnits ────────┼──┼──┼──┼──► MeshUnits(x, y, z)           │
│  │ thresholds: list[float]       │  │  │  │                                 │
│  │ base_height: float            │  │  │  │                                 │
│  │ layer_thickness: float        │  │  │  │                                 │
│  └───────────────────────────────┘  │  │  │                                 │
│                                     ▼  │  │                                 │
│  ┌───────────────────────────────┐    │  │   ┌────────────────────────┐    │
│  │ ContourExtractionConfig       │    │  │   │ ImageProcessingConfig  │    │
│  ├───────────────────────────────┤    │  │   ├────────────────────────┤    │
│  │ min_polygon_area: float       │    │  │   │ max_dimension: int?    │    │
│  │ simplify_tolerance: float     │    │  │   │ region: tuple?         │    │
│  │ max_segments: int             │    │  │   │ fill_nan_values: bool  │    │
│  │ min_area_fraction: float      │    │  │   │ color_map: OrderedDict │    │
│  └───────────────────────────────┘    │  │   │ default_fuzziness      │    │
│                                       ▼  │   └────────────────────────┘    │
│  ┌───────────────────────────────┐      │                                  │
│  │ TriangulationConfig           │      │                                  │
│  ├───────────────────────────────┤      │                                  │
│  │ add_interior_points: bool     │      │                                  │
│  │ interior_point_density: float │      │                                  │
│  └───────────────────────────────┘      │                                  │
│                                         ▼                                   │
│  ┌───────────────────────────────┐  ┌──────────────────────────────┐       │
│  │ PostProcessingConfig          │  │ MeshCombinationConfig        │       │
│  ├───────────────────────────────┤  ├──────────────────────────────┤       │
│  │ remove_degenerate_triangles   │  │ merge_threshold: float       │       │
│  │ remove_duplicated_vertices    │  └──────────────────────────────┘       │
│  │ merge_close_vertices: bool    │                                         │
│  │ target_triangle_count: int?   │                                         │
│  │ voxel_size: float             │                                         │
│  └───────────────────────────────┘                                         │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                             DATA MODEL LAYER                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌────────────────────┐     ┌────────────────────┐     ┌─────────────────┐  │
│  │ RawHeightmapData   │ ──► │ HeightmapData      │ ──► │ MeshData        │  │
│  ├────────────────────┤     ├────────────────────┤     ├─────────────────┤  │
│  │ data: np.ndarray   │     │ data: np.ndarray   │     │ data: o3d.Mesh  │  │
│  │ shape: tuple       │     │ _post_processed    │     └─────────────────┘  │
│  └────────────────────┘     │ post_process()     │                          │
│                             └────────────────────┘                          │
│                                                                              │
│  ┌──────────────────────────┐                                               │
│  │ ThresholdSnapshot        │  ◄── Debug/visualization state               │
│  ├──────────────────────────┤                                               │
│  │ threshold: float         │                                               │
│  │ mesh: TriangleMesh?      │                                               │
│  │ contours: list[Polygon]? │                                               │
│  │ vertices_2d: list?       │                                               │
│  │ triangles: list?         │                                               │
│  └──────────────────────────┘                                               │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            PROCESSING LAYER                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         MeshGenerator                                │    │
│  │                    (Main Orchestrator)                               │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ config: MeshGenerationConfig                                        │    │
│  │ contour_extractor ──────┬──► ContourExtractor                       │    │
│  │ triangulator ───────────┼──► Triangulator                           │    │
│  │ mesh_processor ─────────┼──► MeshPostProcessor                      │    │
│  │ mesh_combiner ──────────┴──► MeshCombiner                           │    │
│  │ threshold_snapshots: dict                                           │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ execute(heightmap) → MeshData                                       │    │
│  │ generate_mesh(heightmap, level_idx, threshold, ...) → Mesh          │    │
│  │ _build_extruded_mesh(polygon, base_height, thickness) → Mesh        │    │
│  │ _create_side_faces(vertices, polygon, n_vertices) → faces           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│           │                                                                  │
│           │ uses                                                            │
│           ▼                                                                  │
│  ┌─────────────────────┐  ┌─────────────────────┐  ┌─────────────────────┐  │
│  │ ContourExtractor    │  │ Triangulator        │  │ MeshPostProcessor   │  │
│  ├─────────────────────┤  ├─────────────────────┤  ├─────────────────────┤  │
│  │ min_polygon_area    │  │ add_interior_points │  │ remove_degenerate   │  │
│  │ simplify_tolerance  │  │ interior_density    │  │ remove_duplicated   │  │
│  │ max_segments        │  ├─────────────────────┤  │ merge_close_vertices│  │
│  │ min_area_fraction   │  │ triangulate_polygon │  ├─────────────────────┤  │
│  ├─────────────────────┤  │  → (verts, tris)    │  │ process_mesh(mesh)  │  │
│  │ extract_contour_    │  └─────────────────────┘  │ quick_cleanup(mesh) │  │
│  │   polygons(hmap,t)  │           │               └─────────────────────┘  │
│  │  → list[Polygon]    │           │                         │              │
│  └─────────────────────┘           │                         │              │
│           │                        │                         │              │
│           │ uses                   │ uses                    │ uses         │
│           ▼                        ▼                         ▼              │
│     ┌──────────┐           ┌─────────────┐          ┌─────────────┐        │
│     │ cv2      │           │ scipy       │          │ open3d      │        │
│     │ skimage  │           │ .Delaunay   │          │ mesh ops    │        │
│     │ shapely  │           │ shapely     │          └─────────────┘        │
│     └──────────┘           └─────────────┘                                  │
│                                                                              │
│  ┌─────────────────────┐                                                    │
│  │ MeshCombiner        │                                                    │
│  ├─────────────────────┤                                                    │
│  │ merge_threshold     │                                                    │
│  ├─────────────────────┤                                                    │
│  │ combine_meshes      │                                                    │
│  │  (list) → Mesh      │                                                    │
│  └─────────────────────┘                                                    │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                        IMAGE PROCESSING LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         ImageProcessor                               │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ config: ImageProcessingConfig                                       │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ load_image(path) → np.ndarray                                       │    │
│  │ process_image_to_heightmap(image) → np.ndarray                      │    │
│  │ fill_nan_values(heightmap) → np.ndarray                             │    │
│  │ extract_dominant_colors(image) → list[tuple]                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│           │                                                                  │
│           │ uses                                                            │
│           ▼                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                          ColorMapper                                 │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ color_map: OrderedDict  (hex → {value, fuzziness})                  │    │
│  │ default_fuzziness: float                                            │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │ map_pixel_to_value(rgb) → float | None                              │    │
│  │ _hex_to_rgb(hex) → tuple                         [static]           │    │
│  │ _rgb_to_lab(rgb) → tuple                         [static]           │    │
│  │ _color_distance_lab(lab1, lab2) → float          [static]           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Main Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          COMPLETE PIPELINE                                   │
└─────────────────────────────────────────────────────────────────────────────┘

     ┌─────────────┐
     │ Image File  │
     │ (PNG/JPG)   │
     └──────┬──────┘
            │
            ▼
┌───────────────────────────────────────────────────────────────────┐
│                    IMAGE PROCESSING PHASE                          │
│                                                                    │
│   ImageProcessor.load_image()                                      │
│         │                                                          │
│         ▼                                                          │
│   ┌─────────────┐                                                  │
│   │ RGB Image   │                                                  │
│   │ np.ndarray  │                                                  │
│   └──────┬──────┘                                                  │
│          │                                                          │
│          ▼                                                          │
│   ImageProcessor.process_image_to_heightmap()                      │
│         │                                                          │
│         │  ┌────────────────────────────────────────────────┐     │
│         │  │ ColorMapper                                     │     │
│         ├──┤  - RGB → LAB conversion                         │     │
│         │  │  - Color distance matching                      │     │
│         │  │  - Value assignment by fuzziness threshold      │     │
│         │  └────────────────────────────────────────────────┘     │
│         │                                                          │
│         ▼                                                          │
│   ┌─────────────────┐                                              │
│   │ Heightmap       │                                              │
│   │ np.ndarray      │                                              │
│   │ (float values)  │                                              │
│   └────────┬────────┘                                              │
│            │                                                        │
│            │ np.save()                                              │
│            ▼                                                        │
│   ┌─────────────────┐                                              │
│   │  .npy file      │                                              │
│   └─────────────────┘                                              │
└───────────────────────────────────────────────────────────────────┘
            │
            │ np.load()
            ▼
┌───────────────────────────────────────────────────────────────────┐
│                    MESH GENERATION PHASE                           │
│                                                                    │
│   HeightmapData.post_process()                                     │
│         │                                                          │
│         │  - Apply z-scaling (data * units_z + offset)            │
│         │  - Add exterior buffer (padding)                         │
│         ▼                                                          │
│   ┌─────────────────────┐                                          │
│   │ Processed Heightmap │                                          │
│   └─────────┬───────────┘                                          │
│             │                                                       │
│             ▼                                                       │
│   MeshGenerator.execute()                                          │
│             │                                                       │
│             │  For each threshold in config.thresholds:            │
│             │                                                       │
│     ┌───────┴───────────────────────────────────────────────┐     │
│     │                                                        │     │
│     │  1. ContourExtractor.extract_contour_polygons()       │     │
│     │     ┌────────────────────────────────────────────┐    │     │
│     │     │ - Create binary mask (heightmap >= thresh) │    │     │
│     │     │ - cv2.findContours() with RETR_CCOMP       │    │     │
│     │     │ - Build polygons with holes                │    │     │
│     │     │ - Filter by area, simplify geometry        │    │     │
│     │     └────────────────────────────────────────────┘    │     │
│     │            │                                           │     │
│     │            ▼                                           │     │
│     │     ┌────────────────┐                                │     │
│     │     │ list[Polygon]  │                                │     │
│     │     └───────┬────────┘                                │     │
│     │             │                                          │     │
│     │  2. For each polygon:                                 │     │
│     │             │                                          │     │
│     │             ▼                                          │     │
│     │     Triangulator.triangulate_polygon()                │     │
│     │     ┌────────────────────────────────────────────┐    │     │
│     │     │ - Extract boundary points                  │    │     │
│     │     │ - Generate interior points (grid)          │    │     │
│     │     │ - scipy.spatial.Delaunay()                 │    │     │
│     │     │ - Filter triangles inside polygon          │    │     │
│     │     └────────────────────────────────────────────┘    │     │
│     │            │                                           │     │
│     │            ▼                                           │     │
│     │     ┌──────────────────────┐                          │     │
│     │     │ (vertices, triangles)│                          │     │
│     │     └───────────┬──────────┘                          │     │
│     │                 │                                      │     │
│     │                 ▼                                      │     │
│     │     MeshGenerator._build_extruded_mesh()              │     │
│     │     ┌────────────────────────────────────────────┐    │     │
│     │     │ - Create bottom verts (z = base_height)   │    │     │
│     │     │ - Create top verts (z = base + thickness) │    │     │
│     │     │ - Create bottom/top faces                  │    │     │
│     │     │ - Create side faces (walls)                │    │     │
│     │     └────────────────────────────────────────────┘    │     │
│     │            │                                           │     │
│     │            ▼                                           │     │
│     │     ┌────────────────────┐                            │     │
│     │     │ o3d.TriangleMesh   │                            │     │
│     │     └─────────┬──────────┘                            │     │
│     │               │                                        │     │
│     │  3. MeshPostProcessor.process_mesh()                  │     │
│     │     ┌────────────────────────────────────────────┐    │     │
│     │     │ - remove_degenerate_triangles()            │    │     │
│     │     │ - remove_duplicated_vertices()             │    │     │
│     │     │ - remove_duplicated_triangles()            │    │     │
│     │     │ - merge_close_vertices() if enabled        │    │     │
│     │     └────────────────────────────────────────────┘    │     │
│     │            │                                           │     │
│     │            ▼                                           │     │
│     │     ┌────────────────────┐                            │     │
│     │     │ Cleaned Mesh       │                            │     │
│     │     └────────────────────┘                            │     │
│     │                                                        │     │
│     └────────────────────────────────────────────────────────┘     │
│             │                                                       │
│             │ All level meshes                                     │
│             ▼                                                       │
│   MeshCombiner.combine_meshes()                                    │
│         │                                                          │
│         │  - Iteratively add meshes (mesh += next_mesh)           │
│         │  - Merge vertices, compute normals                       │
│         ▼                                                          │
│   ┌─────────────────┐                                              │
│   │ MeshData        │                                              │
│   │ (Combined)      │                                              │
│   └────────┬────────┘                                              │
│            │                                                        │
│            │ o3d.io.write_triangle_mesh()                          │
│            ▼                                                        │
│   ┌─────────────────┐                                              │
│   │ .stl/.ply/.obj  │                                              │
│   └─────────────────┘                                              │
└───────────────────────────────────────────────────────────────────┘
```

---

## Contour Extraction Detail

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              ContourExtractor.extract_contour_polygons()                     │
└─────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────┐
    │ heightmap       │
    │ np.ndarray      │
    │ + threshold     │
    └────────┬────────┘
             │
             ▼
    ┌───────────────────────────────┐
    │ Binary mask                   │
    │ (heightmap >= threshold)      │
    │ .astype(uint8)                │
    └────────────┬──────────────────┘
                 │
        ┌────────┴────────┐
        │                 │
        ▼                 ▼
┌───────────────┐   ┌───────────────────────┐
│ cv2.find      │   │ skimage.measure.      │
│ Contours()    │   │ find_contours()       │
│               │   │                       │
│ RETR_CCOMP    │   │ level=0.5             │
│ CHAIN_APPROX_ │   └───────────┬───────────┘
│ SIMPLE        │               │
└───────┬───────┘               │
        │                       │
        │ hierarchy             │ raw polygons
        │ [Next, Prev,          │
        │  Child, Parent]       │
        │                       │
        └───────────┬───────────┘
                    │
                    ▼
    ┌───────────────────────────────────┐
    │ Build polygons with holes         │
    │                                   │
    │ For each external (parent == -1): │
    │   - Convert coords to Polygon     │
    │   - Find child contours (holes)   │
    │   - Create Polygon(ext, holes=[]) │
    └─────────────────┬─────────────────┘
                      │
                      ▼
    ┌───────────────────────────────────┐
    │ Union/Difference for nesting      │
    │ shapely.ops.unary_union()         │
    └─────────────────┬─────────────────┘
                      │
                      ▼
    ┌───────────────────────────────────┐
    │ _filter_and_simplify_polygons()   │
    │                                   │
    │ - Filter: area >= min_fraction *  │
    │           max_area                │
    │ - Simplify until max_segments     │
    └─────────────────┬─────────────────┘
                      │
                      ▼
    ┌───────────────────────────────────┐
    │ Handle inverted cases             │
    │ (hole area > exterior area)       │
    └─────────────────┬─────────────────┘
                      │
                      ▼
              ┌───────────────┐
              │ list[Polygon] │
              └───────────────┘
```

---

## Triangulation Detail

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                  Triangulator.triangulate_polygon()                          │
└─────────────────────────────────────────────────────────────────────────────┘

         ┌────────────────┐
         │ Polygon        │
         │ (with holes)   │
         └───────┬────────┘
                 │
                 ▼
    ┌────────────────────────────┐
    │ _extract_boundary_points() │
    │                            │
    │ exterior.coords → points   │
    │ + hole.coords → points     │
    └─────────────┬──────────────┘
                  │
                  ▼
    ┌────────────────────────────┐
    │ _generate_interior_points()│
    │                            │
    │ if add_interior_points:    │
    │   - Create grid over bbox  │
    │   - Filter points inside   │
    │     polygon                │
    │   - Density controls       │
    │     spacing                │
    └─────────────┬──────────────┘
                  │
                  ▼
    ┌────────────────────────────┐
    │ All points combined        │
    │ (boundary + interior)      │
    └─────────────┬──────────────┘
                  │
                  ▼
    ┌────────────────────────────┐
    │ scipy.spatial.Delaunay()   │
    │                            │
    │ Computes triangulation     │
    │ of all points              │
    └─────────────┬──────────────┘
                  │
                  ▼
    ┌────────────────────────────┐
    │ _filter_interior_triangles │
    │                            │
    │ For each triangle:         │
    │   - Compute centroid       │
    │   - Check if centroid is   │
    │     inside polygon         │
    │   - Discard if in hole     │
    └─────────────┬──────────────┘
                  │
                  ▼
    ┌─────────────────────────────┐
    │ (vertices: np.ndarray,      │
    │  triangles: np.ndarray)     │
    │                             │
    │ vertices: (N, 2) float      │
    │ triangles: (M, 3) int       │
    └─────────────────────────────┘
```

---

## Mesh Extrusion Detail

```
┌─────────────────────────────────────────────────────────────────────────────┐
│              MeshGenerator._build_extruded_mesh()                            │
└─────────────────────────────────────────────────────────────────────────────┘

         ┌─────────────────────────┐
         │ Polygon + triangulation │
         │ + base_height           │
         │ + thickness             │
         └────────────┬────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │ Create bottom vertices              │
    │                                     │
    │ For each (x, y) in vertices_2d:     │
    │   bottom_v.append([x, y, base])     │
    └─────────────────┬───────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │ Create top vertices                 │
    │                                     │
    │ For each (x, y) in vertices_2d:     │
    │   top_v.append([x, y, base+thick])  │
    └─────────────────┬───────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │ Create bottom faces                 │
    │                                     │
    │ bottom_faces = triangles            │
    │ (reversed winding for bottom)       │
    └─────────────────┬───────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │ Create top faces                    │
    │                                     │
    │ top_faces = triangles + n_vertices  │
    │ (offset indices for top layer)      │
    └─────────────────┬───────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │ _create_side_faces()                │
    │                                     │
    │ For each boundary edge (i → i+1):   │
    │                                     │
    │   top[i]─────────top[i+1]           │
    │     │  ╲           │                │
    │     │    ╲  tri2   │                │
    │     │      ╲       │                │
    │     │  tri1  ╲     │                │
    │     │          ╲   │                │
    │   bot[i]─────────bot[i+1]           │
    │                                     │
    │   tri1: [bot[i], bot[i+1], top[i]]  │
    │   tri2: [top[i], bot[i+1], top[i+1]]│
    └─────────────────┬───────────────────┘
                      │
                      ▼
    ┌─────────────────────────────────────┐
    │ Combine all:                        │
    │                                     │
    │ vertices = bottom_v + top_v         │
    │ faces = bottom + top + sides        │
    │                                     │
    │ _create_mesh_from_vertices_faces()  │
    └─────────────────┬───────────────────┘
                      │
                      ▼
              ┌───────────────────┐
              │ o3d.TriangleMesh  │
              │ (extruded solid)  │
              └───────────────────┘
```

---

## Module Dependencies

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          DEPENDENCY GRAPH                                    │
└─────────────────────────────────────────────────────────────────────────────┘

bathy.workflows.generate_mesh
    │
    ├──► bathy.config
    ├──► bathy.data_model
    ├──► bathy.mesh_generator ──┬──► bathy.contour_extractor ──► cv2, skimage, shapely
    │                           ├──► bathy.triangulator ──────► scipy.spatial, shapely
    │                           ├──► bathy.mesh_post_processor ──► open3d
    │                           └──► bathy.mesh_combiner ──────► open3d
    └──► open3d (io)

bathy.workflows.process_image
    │
    ├──► bathy.config
    ├──► bathy.data_model
    └──► bathy.image_processing.image_processor
              │
              ├──► bathy.image_processing.color_mapper
              ├──► PIL (Image)
              ├──► skimage.color (rgb2lab)
              ├──► sklearn.cluster (KMeans)
              └──► numpy

External Dependencies:
┌────────────────┬──────────────────────────────────────────────┐
│ Package        │ Purpose                                      │
├────────────────┼──────────────────────────────────────────────┤
│ numpy          │ Array ops, heightmap data                    │
│ open3d         │ 3D mesh creation/manipulation/export         │
│ shapely        │ Polygon geometry, spatial ops                │
│ opencv-python  │ Contour detection                            │
│ scikit-image   │ Contour extraction, LAB color conversion     │
│ scipy          │ Delaunay triangulation                       │
│ PIL/Pillow     │ Image loading                                │
│ sklearn        │ KMeans for dominant color extraction         │
│ matplotlib     │ Visualization                                │
│ tqdm           │ Progress bars                                │
└────────────────┴──────────────────────────────────────────────┘
```

---

## Public API Reference

```python
# High-level workflows
from bathy.workflows.process_image import process_image
from bathy.workflows.generate_mesh import generate_mesh

# Configs
from bathy.config import (
    MeshGenerationConfig,
    ImageProcessingConfig,
    HeighmapProcessingConfig,
    MeshUnits,
    ContourExtractionConfig,
    TriangulationConfig,
    PostProcessingConfig,
    MeshCombinationConfig,
)

# Data models
from bathy.data_model import HeightmapData, MeshData, RawHeightmapData

# Core processors
from bathy.mesh_generator import MeshGenerator
from bathy.contour_extractor import ContourExtractor
from bathy.triangulator import Triangulator
from bathy.mesh_combiner import MeshCombiner
from bathy.mesh_post_processor import MeshPostProcessor
from bathy.image_processing.image_processor import ImageProcessor
from bathy.image_processing.color_mapper import ColorMapper

# Visualization
from bathy.viz.heightmap import heightmap_plot
from bathy.viz.contours import contour_plot
```

---

## Summary

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ARCHITECTURE LAYERS                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    WORKFLOW LAYER                                    │    │
│  │              (generate_mesh, process_image)                          │    │
│  │                    Entry points                                      │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                  ORCHESTRATION LAYER                                 │    │
│  │                    (MeshGenerator)                                   │    │
│  │               Coordinates all processors                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                   PROCESSING LAYER                                   │    │
│  │   ContourExtractor │ Triangulator │ MeshPostProcessor │ MeshCombiner│    │
│  │                    Specialized processors                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    DATA MODEL LAYER                                  │    │
│  │          RawHeightmapData → HeightmapData → MeshData                │    │
│  │                    Typed data containers                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                  CONFIGURATION LAYER                                 │    │
│  │                MeshGenerationConfig + sub-configs                    │    │
│  │                   All parameters defined                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

Design patterns:
  - Factory: from_config() class methods
  - Composition: MeshGenerator contains specialized processors
  - Dataclasses: All configs and data models
  - Pipeline: Clear data transformation stages
```
