use super::mesh::Mesh;

pub struct MeshCombiner;

impl MeshCombiner {
    pub fn new() -> Self {
        Self
    }

    /// Combine multiple meshes into a single mesh
    pub fn combine_meshes(&self, meshes: &[Mesh]) -> Mesh {
        if meshes.is_empty() {
            return Mesh::empty();
        }

        let mut combined_vertices = Vec::new();
        let mut combined_indices = Vec::new();
        let mut vertex_offset = 0u32;

        for mesh in meshes {
            // Add vertices
            combined_vertices.extend_from_slice(&mesh.vertices);

            // Add indices with offset
            for &index in &mesh.indices {
                combined_indices.push(index + vertex_offset);
            }

            vertex_offset += mesh.vertices.len() as u32;
        }

        println!("Combined {} meshes into {} vertices and {} triangles",
                 meshes.len(), combined_vertices.len(), combined_indices.len() / 3);

        Mesh::new(combined_vertices, combined_indices)
    }

    /// Combine meshes from multiple layers
    pub fn combine_layers(&self, layers: &[Vec<Mesh>]) -> Mesh {
        let all_meshes: Vec<&Mesh> = layers.iter().flat_map(|layer| layer.iter()).collect();
        let meshes_vec: Vec<Mesh> = all_meshes.iter().map(|&m| m.clone()).collect();
        self.combine_meshes(&meshes_vec)
    }
}
