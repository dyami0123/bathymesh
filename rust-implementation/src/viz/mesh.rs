use anyhow::Result;
use rerun::RecordingStreamBuilder;

use crate::core::Mesh;

pub struct MeshVisualizer;

impl MeshVisualizer {
    pub fn new() -> Self {
        Self
    }

    /// Visualize a mesh in Rerun
    pub fn visualize_mesh(
        &self,
        mesh: &Mesh,
        entity_path: &str,
        app_name: &str,
    ) -> Result<()> {
        println!("Starting Rerun visualization for mesh with {} vertices and {} triangles",
                 mesh.vertex_count(), mesh.triangle_count());

        // Initialize Rerun
        let rec = RecordingStreamBuilder::new(app_name)
            .spawn()?;

        // Log the mesh
        rec.log(
            entity_path,
            &rerun::Mesh3D::new(mesh.vertices.clone())
                .with_triangle_indices(
                    mesh.indices
                        .chunks(3)
                        .map(|chunk| [chunk[0], chunk[1], chunk[2]])
                        .collect::<Vec<_>>()
                ),
        )?;

        // Log metadata
        rec.log(
            format!("{}/info", entity_path),
            &rerun::TextDocument::new(format!(
                "Mesh Statistics\n\
                 Vertices: {}\n\
                 Triangles: {}",
                mesh.vertex_count(),
                mesh.triangle_count()
            )),
        )?;

        println!("Rerun mesh visualization ready!");

        Ok(())
    }

    /// Visualize multiple mesh layers with color-coding and edge outlines
    pub fn visualize_layers(
        &self,
        layers: &[(f64, Vec<Mesh>)],
        app_name: &str,
    ) -> Result<()> {
        println!("Starting Rerun visualization for {} layers", layers.len());

        // Initialize Rerun
        let rec = RecordingStreamBuilder::new(app_name)
            .spawn()?;

        // Find min/max heights for color mapping and layer thickness calculation
        let heights: Vec<f64> = layers.iter().map(|(h, _)| *h).collect();
        let min_height = heights.iter().copied().fold(f64::INFINITY, f64::min);
        let max_height = heights.iter().copied().fold(f64::NEG_INFINITY, f64::max);
        
        // Calculate average layer thickness for offset
        let layer_thickness = if heights.len() > 1 {
            (max_height - min_height) / (heights.len() - 1) as f64
        } else {
            30.0 // Default thickness if only one layer
        };
        let z_offset = (layer_thickness * 0.05) as f32; // 5% offset

        for (threshold, meshes) in layers {
            // Calculate color based on height (viridis-like gradient)
            let normalized = if max_height > min_height {
                (threshold - min_height) / (max_height - min_height)
            } else {
                0.5
            };
            let color = height_to_color(normalized as f32);

            for (i, mesh) in meshes.iter().enumerate() {
                let entity_path = format!("mesh/layer_{:.0}/mesh_{}", threshold, i);
                
                // Log the mesh with color
                rec.log(
                    entity_path.as_str(),
                    &rerun::Mesh3D::new(mesh.vertices.clone())
                        .with_triangle_indices(
                            mesh.indices
                                .chunks(3)
                                .map(|chunk| [chunk[0], chunk[1], chunk[2]])
                                .collect::<Vec<_>>()
                        )
                        .with_vertex_colors(vec![color; mesh.vertices.len()]),
                )?;

                // Add edge outlines with Z offset
                let (boundary_edges, interior_edges) = extract_edges(mesh);
                
                // Draw boundary edges (outer contour) in thicker black
                let offset_boundary: Vec<Vec<[f32; 3]>> = boundary_edges.iter().map(|edge| {
                    edge.iter().map(|&[x, y, z]| [x, y, z + z_offset]).collect()
                }).collect();
                
                if !offset_boundary.is_empty() {
                    rec.log(
                        format!("{}/boundary_edges", entity_path),
                        &rerun::LineStrips3D::new(offset_boundary)
                            .with_colors([rerun::Color::from_rgb(0, 0, 0)])
                            .with_radii([1.2]),
                    )?;
                }
                
                // Draw interior edges (triangulation) in thinner gray
                let offset_interior: Vec<Vec<[f32; 3]>> = interior_edges.iter().map(|edge| {
                    edge.iter().map(|&[x, y, z]| [x, y, z + z_offset]).collect()
                }).collect();
                
                if !offset_interior.is_empty() {
                    rec.log(
                        format!("{}/interior_edges", entity_path),
                        &rerun::LineStrips3D::new(offset_interior)
                            .with_colors([rerun::Color::from_rgb(100, 100, 100)])
                            .with_radii([0.2]),
                    )?;
                }

                // Add vertex points with Z offset
                let offset_vertices: Vec<[f32; 3]> = mesh.vertices.iter()
                    .map(|&[x, y, z]| [x, y, z + z_offset])
                    .collect();
                
                rec.log(
                    format!("{}/vertices", entity_path),
                    &rerun::Points3D::new(offset_vertices)
                        .with_colors([rerun::Color::from_rgb(50, 50, 50)])
                        .with_radii([0.8]),
                )?;
            }
        }

        println!("Rerun layer visualization ready!");

        Ok(())
    }
}

/// Convert normalized height (0-1) to a viridis-like color
fn height_to_color(t: f32) -> rerun::Color {
    let t = t.clamp(0.0, 1.0);
    
    // Viridis gradient: purple (low) -> blue -> green -> yellow (high)
    let r = if t < 0.5 {
        (0.267 + t * 0.2) * 255.0
    } else {
        (0.367 + (t - 0.5) * 1.2) * 255.0
    };
    
    let g = if t < 0.5 {
        (0.004 + t * 0.8) * 255.0
    } else {
        (0.404 + (t - 0.5) * 1.0) * 255.0
    };
    
    let b = if t < 0.5 {
        (0.329 + t * 0.8) * 255.0
    } else {
        (0.729 - (t - 0.5) * 1.4) * 255.0
    };

    rerun::Color::from_rgb(
        r.clamp(0.0, 255.0) as u8,
        g.clamp(0.0, 255.0) as u8,
        b.clamp(0.0, 255.0) as u8,
    )
}

/// Extract edges from a mesh, separating boundary edges from interior edges
fn extract_edges(mesh: &Mesh) -> (Vec<Vec<[f32; 3]>>, Vec<Vec<[f32; 3]>>) {
    use std::collections::HashMap;
    
    let mut edge_count: HashMap<(u32, u32), usize> = HashMap::new();
    
    // Count how many times each edge appears
    for triangle in mesh.indices.chunks(3) {
        if triangle.len() == 3 {
            let v0 = triangle[0];
            let v1 = triangle[1];
            let v2 = triangle[2];
            
            // Add edges (use sorted order for consistent keys)
            *edge_count.entry((v0.min(v1), v0.max(v1))).or_insert(0) += 1;
            *edge_count.entry((v1.min(v2), v1.max(v2))).or_insert(0) += 1;
            *edge_count.entry((v2.min(v0), v2.max(v0))).or_insert(0) += 1;
        }
    }
    
    // Separate boundary edges (appear once) from interior edges (appear twice)
    let mut boundary_edges = Vec::new();
    let mut interior_edges = Vec::new();
    
    for ((i0, i1), count) in edge_count.iter() {
        let edge = vec![
            mesh.vertices[*i0 as usize],
            mesh.vertices[*i1 as usize],
        ];
        
        if *count == 1 {
            boundary_edges.push(edge);
        } else {
            interior_edges.push(edge);
        }
    }
    
    (boundary_edges, interior_edges)
}
