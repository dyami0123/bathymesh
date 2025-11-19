use anyhow::{Context, Result};
use clap::Parser;
use image::GenericImageView;
use std::fs::File;
use std::io::Write;
use std::path::PathBuf;

use rust_implementation::config::ImageConfig;
use rust_implementation::image_processor::ImageProcessor;
use rust_implementation::viz::HeightmapVisualizer;

#[derive(Parser, Debug)]
#[command(author, version, about, long_about = None)]
struct Args {
    /// Path to the image file
    #[arg(short, long)]
    image: PathBuf,

    /// Path to the configuration file
    #[arg(short, long)]
    config: PathBuf,

    /// Path to save the output heightmap (raw f64 bytes)
    #[arg(short, long)]
    output: PathBuf,

    /// Launch Rerun visualization
    #[arg(short, long)]
    rerun: bool,
}

fn main() -> Result<()> {
    let args = Args::parse();

    println!("Bathymesh Rust Prototype");
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
    let heightmap = processor.process_image_to_heightmap(&image, &config.processing)?;

    // Save output
    // For simplicity, we'll save as raw bytes (f64 little endian)
    // Python can read this with np.fromfile(path, dtype=np.float64).reshape(h, w)
    let mut file = File::create(&args.output).context("Failed to create output file")?;
    
    // Write dimensions first? No, let's just write raw data.
    // Actually, to be useful, we should probably print dimensions so user knows how to reshape.
    let (width, height) = image.dimensions();
    println!("Output dimensions: {}x{}", width, height);
    
    let buffer: Vec<u8> = heightmap
        .iter()
        .flat_map(|v| v.to_le_bytes().to_vec())
        .collect();
        
    file.write_all(&buffer).context("Failed to write output file")?;
    
    println!("Saved heightmap to {:?}", args.output);

    // Launch Rerun visualization if requested
    if args.rerun {
        let visualizer = HeightmapVisualizer::new();
        visualizer.visualize_heightmap(
            &heightmap,
            width as usize,
            height as usize,
            "Bathymesh Heightmap",
        )?;
    }

    Ok(())
}
