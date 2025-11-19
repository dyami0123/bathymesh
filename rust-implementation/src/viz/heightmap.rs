use anyhow::Result;
use rerun::{RecordingStreamBuilder, external::glam};

pub struct Visualizer;

impl Visualizer {
    pub fn new() -> Self {
        Self
    }

    pub fn visualize_heightmap(
        &self,
        heightmap: &[f64],
        width: usize,
        height: usize,
        app_name: &str,
    ) -> Result<()> {
        println!("Starting Rerun visualization for heightmap");

        // Initialize Rerun
        let rec = RecordingStreamBuilder::new(app_name)
            .spawn()?;

        // Log the original image as a depth map
        let shape = vec![
            rerun::TensorDimension::height(height as u64),
            rerun::TensorDimension::width(width as u64),
        ];
        let buffer = rerun::TensorBuffer::F32(
            heightmap.iter().map(|&v| v as f32).collect::<Vec<f32>>().into()
        );
        let tensor_data = rerun::TensorData::new(shape, buffer);
        
        rec.log(
            "heightmap/depth",
            &rerun::DepthImage::try_from(tensor_data)?,
        )?;

        // Create a 3D point cloud from the heightmap
        let mut positions = Vec::new();
        let mut colors = Vec::new();

        // Find min/max for color normalization
        let valid_values: Vec<f64> = heightmap.iter().filter(|v| !v.is_nan()).copied().collect();
        let min_val = valid_values.iter().copied().fold(f64::INFINITY, f64::min);
        let max_val = valid_values.iter().copied().fold(f64::NEG_INFINITY, f64::max);

        println!("Height range: {:.2} to {:.2}", min_val, max_val);

        // Sample points (use every Nth point to avoid overwhelming the viewer)
        let sample_rate = 4; // Adjust this to control point density
        for y in (0..height).step_by(sample_rate) {
            for x in (0..width).step_by(sample_rate) {
                let idx = y * width + x;
                let z = heightmap[idx];

                if !z.is_nan() {
                    // Position: X, Y (image coords), Z (height)
                    positions.push(glam::Vec3::new(x as f32, y as f32, z as f32));

                    // Color based on height (viridis-like gradient)
                    let normalized = ((z - min_val) / (max_val - min_val)) as f32;
                    let color = viridis_color(normalized);
                    colors.push(color);
                }
            }
        }

        println!("Logging {} points to Rerun", positions.len());

        let num_points = positions.len();

        // Log the 3D point cloud
        rec.log(
            "heightmap/points",
            &rerun::Points3D::new(positions)
                .with_colors(colors)
                .with_radii([0.5]), // Point size
        )?;

        // Log metadata
        rec.log(
            "heightmap/info",
            &rerun::TextDocument::new(format!(
                "Heightmap Visualization\n\
                 Dimensions: {}x{}\n\
                 Height range: {:.2} to {:.2}\n\
                 Total points: {}",
                width, height, min_val, max_val, num_points
            )),
        )?;

        println!("Rerun visualization ready! Open the Rerun viewer to see the data.");

        Ok(())
    }
}

// Simple viridis-like color gradient
fn viridis_color(t: f32) -> rerun::Color {
    // Simplified viridis gradient (purple -> blue -> green -> yellow)
    let t = t.clamp(0.0, 1.0);
    
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

