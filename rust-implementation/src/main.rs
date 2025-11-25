use anyhow::{Context, Result};
use clap::Parser;
use image::GenericImageView;
use std::fs::File;
use std::io::Write;
use std::path::PathBuf;

use rust_implementation::config::ImageConfig;
use rust_implementation::core::{ContourExtractor, MeshCombiner, MeshGenerator};
use rust_implementation::image_processor::ImageProcessor;
use rust_implementation::viz::{ContourVisualizer, HeightmapVisualizer, MeshVisualizer};

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to the image file
    #[arg(short, long)]
    image: PathBuf,

    /// Path to the configuration file
    #[arg(short, long)]
    config: PathBuf,

    /// Launch Rerun visualization
    #[arg(short, long)]
    rerun: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();

    println!("Bathymesh Rust");
    println!("------------------------");

    // Load config
    let config = ImageConfig::load_from_yaml(&args.config)?;
    println!("Loaded config from {:?}", args.config);

    // Initialize processor
    let processor = ImageProcessor::new();

    // Load image
    let image = processor.load_image(
        &args.image,
        config.source.preserve_full_resolution,
        config.source.max_dimension,
    )?;

    // Process image
    let heightmap = processor.process_image_to_heightmap(&image, &config.image_processing)?;

    let (width, height) = image.dimensions();
    println!("Heightmap dimensions: {}x{}", width, height);

    // Extract contours at multiple thresholds
    let thresholds = &config.mesh_generation.thresholds;

    let extractor = ContourExtractor::new(config.contour_generation);
    let snapshots = extractor.extract_multi_threshold(
        &heightmap,
        width as usize,
        height as usize,
        thresholds,
    )?;

    println!("Extracted contours at {} threshold levels", snapshots.len());

    // Generate extruded meshes for each layer
    let mesh_generator = MeshGenerator::new(config.mesh_generation.clone());
    let mut layers = Vec::new();

    for (i, snapshot) in snapshots.iter().enumerate() {
        let level_height = config.mesh_generation.base_height
            + (i as f64 * config.mesh_generation.layer_thickness);

        println!(
            "Generating layer {} at threshold {:.0}, height {:.1}",
            i, snapshot.threshold, level_height
        );

        let meshes =
            mesh_generator.generate_extruded_mesh(&snapshot.contours, Some(level_height))?;

        println!(
            "  Generated {} meshes with {} total triangles",
            meshes.len(),
            meshes.iter().map(|m| m.triangle_count()).sum::<usize>()
        );

        layers.push((snapshot.threshold, meshes));
    }

    // Combine all layers into a single mesh
    let combiner = MeshCombiner::new();
    let combined_mesh =
        combiner.combine_layers(&layers.iter().map(|(_, m)| m.clone()).collect::<Vec<_>>());

    println!("\nCombined mesh statistics:");
    println!("  Vertices: {}", combined_mesh.vertex_count());
    println!("  Triangles: {}", combined_mesh.triangle_count());

    // Create unique app IDs with timestamps to avoid state persistence
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap()
        .as_secs();

    let app_name = format!("Bathymesh Complete View {}", timestamp);

    if args.rerun {
        // Visualize the heightmap first (as a reference layer)
        println!("\nVisualizing heightmap...");
        let heightmap_viz = HeightmapVisualizer::new();
        heightmap_viz.visualize_heightmap(
            &heightmap,
            width as usize,
            height as usize,
            &app_name,
        )?;

        // Visualize contours in the same recording
        println!("Visualizing contours...");
        let contour_viz = ContourVisualizer::new();
        contour_viz.visualize_contours(&snapshots, &app_name)?;

        // Visualize individual mesh layers in the same recording
        println!("Visualizing mesh layers...");
        let visualizer = MeshVisualizer::new();
        visualizer.visualize_layers(&layers, &app_name)?;
    }

    Ok(())
}
