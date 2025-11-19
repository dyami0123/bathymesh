use anyhow::Result;
use rerun::RecordingStreamBuilder;

use crate::core::ThresholdSnapshot;

pub struct ContourVisualizer;

impl ContourVisualizer {
    pub fn new() -> Self {
        Self
    }

    /// Visualize contours from threshold snapshots in Rerun
    pub fn visualize_contours(
        &self,
        snapshots: &[ThresholdSnapshot],
        app_name: &str,
    ) -> Result<()> {
        println!("Starting Rerun visualization for {} threshold levels", snapshots.len());

        // Initialize Rerun
        let rec = RecordingStreamBuilder::new(app_name)
            .spawn()?;

        // Log each threshold level
        for snapshot in snapshots {
            let threshold_str = format!("contours/threshold_{:.0}", snapshot.threshold);
            
            println!("Logging {} contours at threshold {:.2}", 
                     snapshot.contours.len(), snapshot.threshold);

            // Convert each polygon to a LineString for visualization
            for (i, polygon) in snapshot.contours.iter().enumerate() {
                let exterior = polygon.exterior();
                
                // Extract points from the exterior ring
                let points: Vec<[f32; 3]> = exterior
                    .points()
                    .map(|p| [p.x() as f32, p.y() as f32, snapshot.threshold as f32])
                    .collect();

                if points.len() >= 2 {
                    // Log as a LineStrip3D
                    rec.log(
                        format!("{}/contour_{}", threshold_str, i),
                        &rerun::LineStrips3D::new([points.clone()])
                            .with_radii([0.5]),
                    )?;
                }
            }

            // Log metadata for this threshold
            rec.log(
                format!("{}/info", threshold_str),
                &rerun::TextDocument::new(format!(
                    "Threshold: {:.2}\nContours: {}",
                    snapshot.threshold,
                    snapshot.contours.len()
                )),
            )?;
        }

        println!("Rerun contour visualization ready!");

        Ok(())
    }
}
