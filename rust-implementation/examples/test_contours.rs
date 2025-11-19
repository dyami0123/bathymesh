use anyhow::Result;
use image::GenericImageView;
use rust_implementation::config::ImageConfig;
use rust_implementation::image_processor::ImageProcessor;
use rust_implementation::core::{ContourExtractor, ContourParams};
use rust_implementation::viz::ContourVisualizer;

fn main() -> Result<()> {
    let args: Vec<String> = std::env::args().collect();
    
    if args.len() < 3 {
        eprintln!("Usage: {} <image> <config>", args[0]);
        std::process::exit(1);
    }

    let image_path = &args[1];
    let config_path = &args[2];

    println!("Bathymesh Contour Visualization Test");
    println!("-------------------------------------");

    // Load config
    let config = ImageConfig::load_from_yaml(config_path)?;
    println!("Loaded config from {:?}", config_path);

    // Initialize processor
    let processor = ImageProcessor::new();

    // Load image
    let image = processor.load_image(
        image_path,
        config.source.preserve_full_resolution,
        config.source.max_dimension,
    )?;

    // Process image
    let heightmap = processor.process_image_to_heightmap(&image, &config.processing)?;
    let (width, height) = image.dimensions();

    println!("Processed heightmap: {}x{}", width, height);

    // Extract contours at multiple thresholds
    let thresholds = vec![0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9];
    let contour_params = ContourParams {
        min_polygon_area: 500.0,
        simplify_tolerance: 2.0,
        max_segments: 100,
        min_area_fraction: 0.01,
    };
    
    let extractor = ContourExtractor::new(contour_params);
    let snapshots = extractor.extract_multi_threshold(
        &heightmap,
        width as usize,
        height as usize,
        &thresholds,
    )?;

    println!("Extracted contours at {} threshold levels", snapshots.len());

    // Visualize contours
    let visualizer = ContourVisualizer::new();
    visualizer.visualize_contours(&snapshots, "Bathymesh Contours")?;

    Ok(())
}
