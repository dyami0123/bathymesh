use anyhow::{Result, bail};
use geo::{Polygon, Contains, Coord};
use delaunator::{triangulate, Point as DelaunatorPoint};

use super::mesh::Mesh;

pub struct Triangulator;

impl Triangulator {
    pub fn new() -> Self {
        Self
    }

    /// Triangulate a polygon at a specific height
    pub fn triangulate_polygon(
        &self,
        polygon: &Polygon<f64>,
        height: f64,
    ) -> Result<Mesh> {
        // Validate polygon
        if polygon.exterior().0.is_empty() {
            bail!("Input polygon has no exterior coordinates");
        }

        let area = geo::Area::unsigned_area(polygon);
        if area == 0.0 {
            bail!("Input polygon has zero area");
        }

        // Extract boundary points (exterior + holes)
        let mut all_points = Vec::new();
        
        // Add exterior ring points (excluding duplicate last point)
        for point in polygon.exterior().points().take(polygon.exterior().0.len() - 1) {
            all_points.push(DelaunatorPoint { x: point.x(), y: point.y() });
        }
        
        let boundary_count = all_points.len();
        
        // Add hole points
        for interior in polygon.interiors() {
            for point in interior.points().take(interior.0.len() - 1) {
                all_points.push(DelaunatorPoint { x: point.x(), y: point.y() });
            }
        }

        println!("Triangulating polygon with {} boundary points ({} exterior, {} holes) at height {:.2}", 
                 all_points.len(), boundary_count, polygon.interiors().len(), height);

        if all_points.len() < 3 {
            return Ok(Mesh::empty());
        }

        // Perform Delaunay triangulation
        let result = triangulate(&all_points);

        // Filter triangles to keep only those inside the polygon
        let valid_triangles = self.filter_interior_triangles(&all_points, &result.triangles, polygon)?;

        if valid_triangles.is_empty() {
            bail!("No valid triangles found inside polygon");
        }

        // Convert to 3D mesh
        let vertices: Vec<[f32; 3]> = all_points
            .iter()
            .map(|p| [p.x as f32, p.y as f32, height as f32])
            .collect();

        println!("Created mesh with {} vertices and {} triangles (filtered from {} total)", 
                 vertices.len(), valid_triangles.len() / 3, result.triangles.len() / 3);

        Ok(Mesh::new(vertices, valid_triangles))
    }

    /// Filter triangles to keep only those with centroids inside the polygon
    fn filter_interior_triangles(
        &self,
        points: &[DelaunatorPoint],
        triangles: &[usize],
        polygon: &Polygon<f64>,
    ) -> Result<Vec<u32>> {
        let mut valid_indices = Vec::new();

        for triangle_indices in triangles.chunks(3) {
            if triangle_indices.len() != 3 {
                continue;
            }

            // Get triangle vertices
            let p0 = &points[triangle_indices[0]];
            let p1 = &points[triangle_indices[1]];
            let p2 = &points[triangle_indices[2]];

            // Calculate centroid
            let centroid_x = (p0.x + p1.x + p2.x) / 3.0;
            let centroid_y = (p0.y + p1.y + p2.y) / 3.0;
            let centroid = Coord { x: centroid_x, y: centroid_y };

            // Check if centroid is inside polygon
            if polygon.contains(&centroid) {
                valid_indices.push(triangle_indices[0] as u32);
                valid_indices.push(triangle_indices[1] as u32);
                valid_indices.push(triangle_indices[2] as u32);
            }
        }

        Ok(valid_indices)
    }

    /// Triangulate multiple polygons at the same height
    pub fn triangulate_layer(
        &self,
        polygons: &[Polygon<f64>],
        height: f64,
    ) -> Result<Vec<Mesh>> {
        let mut meshes = Vec::new();

        for polygon in polygons {
            let mesh = self.triangulate_polygon(polygon, height)?;
            if mesh.triangle_count() > 0 {
                meshes.push(mesh);
            }
        }

        Ok(meshes)
    }
}
