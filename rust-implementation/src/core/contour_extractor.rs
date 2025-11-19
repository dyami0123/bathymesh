use anyhow::Result;
use geo::{Polygon, LineString, Coord};
use geo::algorithm::simplify::Simplify;
use geo::Area;

/// Parameters for contour extraction
#[derive(Debug, Clone)]
pub struct ContourParams {
    pub min_area: f64,
    pub simplify_tolerance: f64,
}

impl Default for ContourParams {
    fn default() -> Self {
        Self {
            min_area: 100.0,
            simplify_tolerance: 1.0,
        }
    }
}

/// Represents a snapshot of contours at a specific threshold
#[derive(Debug, Clone)]
pub struct ThresholdSnapshot {
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
    pub fn extract_contours(
        &self,
        heightmap: &[f64],
        width: usize,
        height: usize,
        threshold: f64,
    ) -> Result<ThresholdSnapshot> {
        println!("Extracting contours at threshold {:.2}", threshold);

        // Create a binary mask where values >= threshold
        let mut mask = vec![0.0; width * height];
        for (i, &value) in heightmap.iter().enumerate() {
            if !value.is_nan() && value >= threshold {
                mask[i] = 1.0;
            }
        }

        // Use the contour crate to extract contours
        let contour_builder = contour::ContourBuilder::new(width, height, false);
        let contours_raw = contour_builder.contours(&mask, &[0.5])?;

        let mut polygons = Vec::new();

        // Convert contours to geo::Polygon
        // The contour crate returns Vec<Band>, where each Band contains MultiPolygon geometry
        for band in contours_raw {
            let geometry = band.geometry();
            // geometry is a MultiPolygon, iterate over its polygons
            for polygon in geometry.0.iter() {
                // Extract exterior ring coordinates
                let coords: Vec<Coord<f64>> = polygon
                    .exterior()
                    .0
                    .iter()
                    .map(|p| Coord { x: p.x, y: p.y })
                    .collect();

                if coords.len() >= 4 {
                    // Need at least 4 points for a valid polygon (including closing point)
                    let line_string = LineString::from(coords);
                    let geo_polygon = Polygon::new(line_string, vec![]);

                    // Filter by area
                    let area = geo_polygon.unsigned_area();
                    if area >= self.params.min_area {
                        // Simplify the polygon
                        let simplified = geo_polygon.simplify(&self.params.simplify_tolerance);
                        polygons.push(simplified);
                    }
                }
            }
        }

        println!("Found {} contours at threshold {:.2}", polygons.len(), threshold);

        Ok(ThresholdSnapshot {
            threshold,
            contours: polygons,
        })
    }

    /// Extract contours at multiple thresholds
    pub fn extract_multi_threshold(
        &self,
        heightmap: &[f64],
        width: usize,
        height: usize,
        thresholds: &[f64],
    ) -> Result<Vec<ThresholdSnapshot>> {
        let mut snapshots = Vec::new();

        for &threshold in thresholds {
            let snapshot = self.extract_contours(heightmap, width, height, threshold)?;
            snapshots.push(snapshot);
        }

        Ok(snapshots)
    }
}
