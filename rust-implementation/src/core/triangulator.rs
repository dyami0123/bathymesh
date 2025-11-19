use anyhow::Result;
use geo::Polygon;
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
        println!("Triangulating polygon with {} vertices at height {:.2}", 
                 polygon.exterior().0.len(), height);

        // Extract points from polygon exterior
        let points: Vec<DelaunatorPoint> = polygon
            .exterior()
            .points()
            .map(|p| DelaunatorPoint { x: p.x(), y: p.y() })
            .collect();

        if points.len() < 3 {
            return Ok(Mesh::empty());
        }

        // Perform Delaunay triangulation
        let result = triangulate(&points);

        // Convert to 3D mesh
        let vertices: Vec<[f32; 3]> = points
            .iter()
            .map(|p| [p.x as f32, p.y as f32, height as f32])
            .collect();

        let indices: Vec<u32> = result.triangles.iter().map(|&i| i as u32).collect();

        println!("Created mesh with {} vertices and {} triangles", 
                 vertices.len(), indices.len() / 3);

        Ok(Mesh::new(vertices, indices))
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
