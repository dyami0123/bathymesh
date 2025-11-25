use super::mesh::Mesh;
use super::triangulator::Triangulator;
use crate::config::mesh_generationParams;
use anyhow::Result;
use geo::Polygon;

pub struct MeshGenerator {
    triangulator: Triangulator,
    params: mesh_generationParams,
}

impl MeshGenerator {
    pub fn new(params: mesh_generationParams) -> Self {
        Self {
            triangulator: Triangulator::new(),
            params,
        }
    }

    pub fn generate_extruded_mesh(
        &self,
        polygons: &[Polygon<f64>],
        base_height_override: Option<f64>,
    ) -> Result<Vec<Mesh>> {
        let mut meshes = Vec::new();

        for polygon in polygons {
            let mesh = self.build_extruded_mesh(polygon, base_height_override)?;
            if mesh.triangle_count() > 0 {
                meshes.push(mesh);
            }
        }

        Ok(meshes)
    }

    fn build_extruded_mesh(
        &self,
        polygon: &Polygon<f64>,
        base_height_override: Option<f64>,
    ) -> Result<Mesh> {
        let base_height = base_height_override.unwrap_or(self.params.base_height);

        // 1. Triangulate the polygon to get the top/bottom face structure (2D)
        // We use base_height for the triangulation, but we'll adjust Z later
        let flat_mesh = self
            .triangulator
            .triangulate_polygon(polygon, base_height)?;

        if flat_mesh.vertex_count() == 0 {
            return Ok(Mesh::empty());
        }

        let n_vertices = flat_mesh.vertex_count();
        let vertices_2d: Vec<[f32; 2]> = flat_mesh.vertices.iter().map(|v| [v[0], v[1]]).collect();

        // 2. Create 3D vertices for bottom and top
        let bottom_z = base_height as f32;
        let top_z = (base_height + self.params.layer_thickness) as f32;

        let mut all_vertices = Vec::with_capacity(n_vertices * 2);

        // Bottom vertices
        for v in &vertices_2d {
            all_vertices.push([v[0], v[1], bottom_z]);
        }

        // Top vertices
        for v in &vertices_2d {
            all_vertices.push([v[0], v[1], top_z]);
        }

        // 3. Create faces
        let mut all_indices = Vec::new();

        // Bottom faces (original winding)
        all_indices.extend_from_slice(&flat_mesh.indices);

        // Top faces (reverse winding + offset)
        // The Python code says: triangles[:, ::-1] + n_vertices
        // In Rust, we iterate chunks of 3 and reverse them
        for chunk in flat_mesh.indices.chunks(3) {
            if chunk.len() == 3 {
                all_indices.push(chunk[2] + n_vertices as u32);
                all_indices.push(chunk[1] + n_vertices as u32);
                all_indices.push(chunk[0] + n_vertices as u32);
            }
        }

        // 4. Create side faces from polygon boundary
        let side_indices = self.create_side_faces(&vertices_2d, polygon, n_vertices);
        all_indices.extend(side_indices);

        Ok(Mesh::new(all_vertices, all_indices))
    }

    fn create_side_faces(
        &self,
        vertices_2d: &[[f32; 2]],
        polygon: &Polygon<f64>,
        n_vertices: usize,
    ) -> Vec<u32> {
        let mut side_indices = Vec::new();

        // Extract boundary coordinates from exterior ring
        // Note: geo-types polygons are closed, so the last point equals the first
        let exterior = polygon.exterior();
        let points = exterior.points().collect::<Vec<_>>();

        if points.len() < 2 {
            return side_indices;
        }

        // Map boundary points to vertex indices
        let boundary_indices = self.map_boundary_to_vertices(&points, vertices_2d);

        if boundary_indices.len() < 2 {
            return side_indices;
        }

        // Create quads (2 triangles) for each edge
        // We iterate up to len-1 because the polygon is closed (first point repeated at end)
        // However, map_boundary_to_vertices might return indices for all points including the duplicate last one
        // Let's check how we handle the loop.

        let loop_count = if points.first() == points.last() {
            boundary_indices.len() - 1
        } else {
            boundary_indices.len()
        };

        for i in 0..loop_count {
            let curr_idx = boundary_indices[i] as u32;
            let next_idx = boundary_indices[(i + 1) % boundary_indices.len()] as u32;

            // Quad vertices:
            // curr_idx (bottom) -> next_idx (bottom)
            // curr_idx + n (top) -> next_idx + n (top)

            // Triangle 1: curr, next, next_top
            side_indices.push(curr_idx);
            side_indices.push(next_idx);
            side_indices.push(next_idx + n_vertices as u32);

            // Triangle 2: curr, next_top, curr_top
            side_indices.push(curr_idx);
            side_indices.push(next_idx + n_vertices as u32);
            side_indices.push(curr_idx + n_vertices as u32);
        }

        side_indices
    }

    fn map_boundary_to_vertices(
        &self,
        boundary_points: &[geo::Point<f64>],
        vertices_2d: &[[f32; 2]],
    ) -> Vec<usize> {
        let mut indices = Vec::new();

        for point in boundary_points {
            let p_x = point.x() as f32;
            let p_y = point.y() as f32;

            // Find closest vertex
            // This is O(N*M) which is naive but matches the Python implementation
            // Optimization: Could use a spatial index if performance becomes an issue

            let mut closest_idx = 0;
            let mut min_dist_sq = f32::MAX;

            for (i, v) in vertices_2d.iter().enumerate() {
                let dx = v[0] - p_x;
                let dy = v[1] - p_y;
                let dist_sq = dx * dx + dy * dy;

                if dist_sq < min_dist_sq {
                    min_dist_sq = dist_sq;
                    closest_idx = i;
                }
            }
            indices.push(closest_idx);
        }

        indices
    }
}
