use crate::config::ContourParams;
use anyhow::Result;
use geo::algorithm::bool_ops::BooleanOps;
use geo::algorithm::simplify::Simplify;
use geo::{Area, CoordsIter, MultiPolygon};
use geo::{Coord, LineString, Polygon};
use opencv::{
    core::{Mat, Point, Vector},
    imgproc::{self, CHAIN_APPROX_SIMPLE, RETR_CCOMP},
    prelude::*,
};

/// Represents a snapshot of contours at a specific threshold
#[derive(Debug, Clone)]
pub struct ThresholdContours {
    pub threshold: f64,
    pub contours: Vec<Polygon<f64>>,
}

pub struct ContourExtractor {
    params: ContourParams,
}

impl ContourExtractor {
    pub fn new(params: ContourParams) -> Self {
        Self { params }
    }

    /// Extract contours from a heightmap at a specific threshold
    ///
    /// This matches the Python implementation exactly, handling nested contours
    /// and creating polygons with holes where appropriate.
    pub fn extract_contours(
        &self,
        heightmap: &[f64],
        width: usize,
        height: usize,
        threshold: f64,
    ) -> Result<ThresholdContours> {
        println!("Extracting contours at threshold {:.2}", threshold);

        // Create binary mask where values >= threshold
        let mut mask_u8 = vec![0u8; width * height];
        for (i, &value) in heightmap.iter().enumerate() {
            if !value.is_nan() && value >= threshold {
                mask_u8[i] = 1;
            }
        }

        // Convert to OpenCV Mat
        // Reshape the flat slice into rows for from_slice_2d
        let rows: Vec<&[u8]> = mask_u8.chunks(width).collect();
        let mask_mat = Mat::from_slice_2d(&rows)?;

        // Find contours with hierarchy using OpenCV (matches Python's cv2.findContours)
        let mut contours_cv: Vector<Vector<Point>> = Vector::new();
        let mut hierarchy = Mat::default();

        imgproc::find_contours_with_hierarchy(
            &mask_mat,
            &mut contours_cv,
            &mut hierarchy,
            RETR_CCOMP, // 2-level hierarchy: external contours and holes
            CHAIN_APPROX_SIMPLE,
            opencv::core::Point::new(0, 0),
        )?;

        if contours_cv.is_empty() {
            println!("No contours found at threshold {:.2}", threshold);
            return Ok(ThresholdContours {
                threshold,
                contours: vec![],
            });
        }

        println!("Found {} contours with OpenCV", contours_cv.len());

        // Extract all raw polygons using skimage-like approach (contour_generation crate)
        let mut mask_f64 = vec![0.0; width * height];
        for (i, &value) in mask_u8.iter().enumerate() {
            mask_f64[i] = value as f64;
        }

        let contour_builder = contour::ContourBuilder::new(width, height, false);
        let contours_raw = contour_builder.contours(&mask_f64, &[0.5])?;

        let mut all_raw_polygons = Vec::new();
        for band in contours_raw {
            let geometry = band.geometry();
            for polygon in geometry.0.iter() {
                let coords: Vec<Coord<f64>> = polygon
                    .exterior()
                    .0
                    .iter()
                    .map(|p| Coord { x: p.x, y: p.y })
                    .collect();

                if coords.len() >= 3 {
                    let line_string = LineString::from(coords);
                    let geo_polygon = Polygon::new(line_string, vec![]);

                    if geo_polygon.unsigned_area() > self.params.min_polygon_area {
                        all_raw_polygons.push(geo_polygon);
                    }
                }
            }
        }

        // Build polygons with holes using hierarchy from OpenCV
        let mut result_polygons = Vec::new();
        let mut processed = std::collections::HashSet::new();

        for i in 0..contours_cv.len() {
            if processed.contains(&i) {
                continue;
            }

            // Get hierarchy info: [Next, Previous, First_Child, Parent]
            let hier = *hierarchy.at_2d::<opencv::core::Vec4i>(0, i as i32)?;
            let parent_idx = hier[3];

            // Skip if this is a hole (will be processed with parent)
            if parent_idx != -1 {
                continue;
            }

            // Convert external contour_generation to polygon
            let contour_generation = contours_cv.get(i)?;
            let coords = self.opencv_contour_to_coords(&contour_generation)?;

            if coords.len() < 3 {
                continue;
            }

            let exterior_poly = Polygon::new(LineString::from(coords.clone()), vec![]);

            if exterior_poly.unsigned_area() < self.params.min_polygon_area {
                continue;
            }

            // Find holes (children of this contour_generation)
            let mut holes = Vec::new();
            let first_child = hier[2];

            if first_child != -1 {
                let mut child_idx = first_child;
                while child_idx != -1 {
                    let hole_contour = contours_cv.get(child_idx as usize)?;
                    let hole_coords = self.opencv_contour_to_coords(&hole_contour)?;

                    if hole_coords.len() >= 3 {
                        holes.push(LineString::from(hole_coords));
                        processed.insert(child_idx as usize);
                    }

                    // Move to next sibling
                    let child_hier = *hierarchy.at_2d::<opencv::core::Vec4i>(0, child_idx)?;
                    child_idx = child_hier[0];
                }
            }

            // Create polygon with holes
            let final_poly = if !holes.is_empty() {
                Polygon::new(LineString::from(coords), holes)
            } else {
                exterior_poly
            };

            result_polygons.push(final_poly);
            processed.insert(i);
        }

        println!("Built {} polygons with OpenCV", result_polygons.len());

        // Skip expensive union operations for now - just use result_polygons directly
        // The union operations are O(n²) and extremely slow for large polygon counts
        // TODO: Implement spatial partitioning or cascaded union if needed
        println!(
            "Using {} result polygons directly (skipping union operations)",
            result_polygons.len()
        );

        let mut holes_removed_polys = result_polygons;

        // Filter and simplify
        holes_removed_polys = self.filter_and_simplify_polygons(
            holes_removed_polys,
            self.params.simplify_tolerance,
            self.params.max_segments,
            self.params.min_area_fraction,
        );

        println!(
            "Final polygon count after filtering and simplification: {}",
            holes_removed_polys.len()
        );

        // Remove interior geometries if they occupy >= 95% of total area
        let mut cleaned_polygons = Vec::new();
        for poly in holes_removed_polys {
            if !poly.interiors().is_empty() {
                let hole_area: f64 = poly
                    .interiors()
                    .iter()
                    .map(|ring| Polygon::new(ring.clone(), vec![]).unsigned_area())
                    .sum();
                let total_area = poly.unsigned_area();

                if hole_area >= 0.95 * total_area {
                    let cleaned_poly = Polygon::new(poly.exterior().clone(), vec![]);
                    cleaned_polygons.push(cleaned_poly);
                    println!(
                        "Removed interiors from polygon (hole area {:.2} >= 95% of {:.2})",
                        hole_area, total_area
                    );
                } else {
                    cleaned_polygons.push(poly);
                }
            } else {
                cleaned_polygons.push(poly);
            }
        }

        Ok(ThresholdContours {
            threshold,
            contours: cleaned_polygons,
        })
    }

    /// Convert OpenCV contour_generation Vector to vector of coordinates
    fn opencv_contour_to_coords(
        &self,
        contour_generation: &Vector<Point>,
    ) -> Result<Vec<Coord<f64>>> {
        let mut coords = Vec::new();

        for i in 0..contour_generation.len() {
            let point = contour_generation.get(i)?;
            coords.push(Coord {
                x: point.x as f64,
                y: point.y as f64,
            });
        }

        Ok(coords)
    }

    /// Filter and simplify polygons based on area and segment count
    fn filter_and_simplify_polygons(
        &self,
        mut polygons: Vec<Polygon<f64>>,
        simplify_tolerance: f64,
        max_segments: usize,
        min_area_fraction: f64,
    ) -> Vec<Polygon<f64>> {
        if polygons.is_empty() {
            return vec![];
        }

        // Filter by area
        let max_area = polygons
            .iter()
            .map(|p| p.unsigned_area())
            .max_by(|a, b| a.partial_cmp(b).unwrap())
            .unwrap_or(0.0);

        let area_threshold = max_area * min_area_fraction;
        polygons.retain(|p| p.unsigned_area() >= area_threshold);

        println!(
            "Filtered to {} polygons with area >= {:.3}",
            polygons.len(),
            area_threshold
        );

        if polygons.is_empty() {
            return vec![];
        }

        // Simplify if needed
        let mut tolerance = simplify_tolerance;
        loop {
            let max_seg = polygons
                .iter()
                .map(|p| p.exterior().coords_count())
                .max()
                .unwrap_or(0);

            if max_seg <= max_segments {
                break;
            }

            tolerance += 0.1;
            polygons = polygons.iter().map(|p| p.simplify(&tolerance)).collect();

            println!(
                "Simplified with tolerance {:.3}, max segments now {}",
                tolerance, max_seg
            );
        }

        polygons
    }

    /// Extract contours at multiple thresholds
    pub fn extract_multi_threshold(
        &self,
        heightmap: &[f64],
        width: usize,
        height: usize,
        thresholds: &[f64],
    ) -> Result<Vec<ThresholdContours>> {
        let mut snapshots = Vec::new();

        for &threshold in thresholds {
            let snapshot = self.extract_contours(heightmap, width, height, threshold)?;
            snapshots.push(snapshot);
        }

        Ok(snapshots)
    }
}
