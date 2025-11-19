use anyhow::{Context, Result};
use image::{GenericImageView, DynamicImage};
use image::imageops::FilterType;
use lab::Lab;
use std::path::Path;
use indicatif::{ProgressBar, ProgressStyle};

use crate::config::ImageProcessingParams;

pub struct ImageProcessor;

impl ImageProcessor {
    pub fn new() -> Self {
        Self
    }

    pub fn load_image<P: AsRef<Path>>(
        &self,
        path: P,
        preserve_full_resolution: bool,
        max_dimension: Option<u32>,
    ) -> Result<DynamicImage> {
        let path = path.as_ref();
        println!("Loading image: {:?}", path);

        let mut img = image::open(path).context("Failed to open image")?;

        if !preserve_full_resolution {
             // In Rust image crate, there isn't a direct "MAX_IMAGE_PIXELS" limit to disable like PIL.
             // It handles large images by default as long as memory allows.
        }

        let (width, height) = img.dimensions();
        println!("Original image size: {}x{}", width, height);

        if let Some(max_dim) = max_dimension {
            let current_max = width.max(height);
            if current_max > max_dim {
                let ratio = max_dim as f64 / current_max as f64;
                let new_width = (width as f64 * ratio) as u32;
                let new_height = (height as f64 * ratio) as u32;
                
                img = img.resize(new_width, new_height, FilterType::Lanczos3);
                println!("Resized to: {}x{}", new_width, new_height);
            }
        }

        Ok(img)
    }

    pub fn process_image_to_heightmap(
        &self,
        image: &DynamicImage,
        params: &ImageProcessingParams,
    ) -> Result<Vec<f64>> {
        let (width, height) = image.dimensions();
        let mut heightmap = vec![f64::NAN; (width * height) as usize];
        
        println!("Processing image of size {}x{} with {} color mappings", width, height, params.color_map.len());

        // Pre-compute LAB values for target colors
        let mut target_colors: Vec<(Lab, f64, f64)> = Vec::new();
        for (hex_color, config) in &params.color_map {
            let rgb = hex_to_rgb(hex_color).context(format!("Invalid hex color: {}", hex_color))?;
            let lab = Lab::from_rgb(&[rgb[0], rgb[1], rgb[2]]);
            target_colors.push((lab, config.value, config.fuzziness));
        }

        let rgb_image = image.to_rgb8();
        let pixels: Vec<_> = rgb_image.pixels().collect();
        let total_pixels = pixels.len();

        let pb = ProgressBar::new(total_pixels as u64);
        pb.set_style(ProgressStyle::default_bar()
            .template("{spinner:.green} [{elapsed_precise}] [{bar:40.cyan/blue}] {pos}/{len} ({eta})")
            .unwrap()
            .progress_chars("#>-"));

        // Process pixels
        // Note: This is single-threaded for now as requested.
        // Rayon could parallelize this easily: `pixels.par_iter().enumerate()...`
        
        let mut matched_pixels = 0;

        for (i, pixel) in pixels.iter().enumerate() {
            let lab_pixel = Lab::from_rgb(&[pixel[0], pixel[1], pixel[2]]);

            for (target_lab, value, fuzziness) in &target_colors {
                // Euclidean distance in LAB space
                let l_diff = lab_pixel.l - target_lab.l;
                let a_diff = lab_pixel.a - target_lab.a;
                let b_diff = lab_pixel.b - target_lab.b;
                let distance = (l_diff * l_diff + a_diff * a_diff + b_diff * b_diff).sqrt();

                if distance as f64 <= *fuzziness {
                    // Check if we already have a value (handle overlaps? Python implementation overwrites based on order)
                    // The Python implementation iterates through colors and overwrites. 
                    // Here we iterate pixels then colors. To match Python exactly, we should respect the order of colors.
                    // However, the params.color_map is a HashMap (unordered). 
                    // Ideally, the config should be a list to preserve order.
                    // For now, we'll just take the first match or overwrite. 
                    // Since we're iterating colors inside the pixel loop, the *last* matching color in `target_colors` will win.
                    // `target_colors` order depends on HashMap iteration order which is random.
                    // TODO: Change config to use Vec for ordered color map.
                    
                    if heightmap[i].is_nan() {
                         matched_pixels += 1;
                    }
                    heightmap[i] = *value;
                }
            }
            
            if i % 10000 == 0 {
                pb.inc(10000);
            }
        }
        pb.finish_with_message("Done");

        let match_percentage = (matched_pixels as f64 / total_pixels as f64) * 100.0;
        println!("Matched {}/{} pixels ({:.1}%)", matched_pixels, total_pixels, match_percentage);

        if params.fill_nan_values {
            heightmap = self.fill_nan_values(heightmap, width as usize, height as usize, params.fill_max_iterations, params.fill_neighborhood_size);
        }

        Ok(heightmap)
    }

    fn fill_nan_values(
        &self,
        mut heightmap: Vec<f64>,
        width: usize,
        height: usize,
        max_iterations: usize,
        neighborhood_size: usize,
    ) -> Vec<f64> {
        let initial_nan_count = heightmap.iter().filter(|v| v.is_nan()).count();
        if initial_nan_count == 0 {
            println!("No NaN values found - skipping fill operation");
            return heightmap;
        }

        println!("Starting NaN filling: {} NaN pixels to fill", initial_nan_count);

        let pb = ProgressBar::new(max_iterations as u64);
        
        for _iteration in 0..max_iterations {
            let mut new_heightmap = heightmap.clone();
            let mut pixels_filled_this_iteration = 0;

            for y in 0..height {
                for x in 0..width {
                    let idx = y * width + x;
                    if heightmap[idx].is_nan() {
                        // Find neighbors
                        let mut sum = 0.0;
                        let mut count = 0;

                        let y_start = y.saturating_sub(neighborhood_size);
                        let y_end = (y + neighborhood_size + 1).min(height);
                        let x_start = x.saturating_sub(neighborhood_size);
                        let x_end = (x + neighborhood_size + 1).min(width);

                        for ny in y_start..y_end {
                            for nx in x_start..x_end {
                                let nidx = ny * width + nx;
                                if !heightmap[nidx].is_nan() {
                                    sum += heightmap[nidx];
                                    count += 1;
                                }
                            }
                        }

                        if count > 0 {
                            let avg = sum / count as f64;
                            new_heightmap[idx] = avg;
                            pixels_filled_this_iteration += 1;
                        }
                    } else {
                        // Calculate change (though for non-nan pixels it shouldn't change in this logic)
                    }
                }
            }

            if pixels_filled_this_iteration == 0 {
                break;
            }
            
            // Calculate change for convergence (simplified)
            // In Python: change = np.nanmean(np.abs(filled_heightmap - old_heightmap))
            // Here we just check if we filled anything.
            
            heightmap = new_heightmap;
            pb.inc(1);
        }
        pb.finish();

        let final_nan_count = heightmap.iter().filter(|v| v.is_nan()).count();
        let filled = initial_nan_count - final_nan_count;
        println!("NaN filling complete: {}/{} pixels filled", filled, initial_nan_count);

        heightmap
    }
}

fn hex_to_rgb(hex: &str) -> Result<[u8; 3]> {
    let hex = hex.trim_start_matches('#');
    if hex.len() != 6 {
        return Err(anyhow::anyhow!("Invalid hex length"));
    }
    let r = u8::from_str_radix(&hex[0..2], 16)?;
    let g = u8::from_str_radix(&hex[2..4], 16)?;
    let b = u8::from_str_radix(&hex[4..6], 16)?;
    Ok([r, g, b])
}
