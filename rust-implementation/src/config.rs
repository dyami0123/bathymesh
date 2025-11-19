use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs::File;
use std::path::Path;
use anyhow::{Context, Result};

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ImageSourceParams {
    #[serde(default = "default_true")]
    pub preserve_full_resolution: bool,
    pub max_dimension: Option<u32>,
    pub region: Option<(u32, u32, u32, u32)>,
}

impl Default for ImageSourceParams {
    fn default() -> Self {
        Self {
            preserve_full_resolution: true,
            max_dimension: None,
            region: None,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ColorMapping {
    pub value: f64,
    pub fuzziness: f64,
}

// Helper to handle the union type from Python (float or dict)
// In Rust, we'll normalize to the struct format during deserialization if possible,
// but for now, let's assume the full struct format for simplicity or use a custom deserializer.
// To match the Python flexibility: "color": {"value": 10.0, "fuzziness": 5.0}
// The Python code also allowed "color": 10.0 (implying default fuzziness).
// Let's stick to the explicit dict format for now to keep it simple.

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct ImageProcessingParams {
    #[serde(default)]
    pub color_map: HashMap<String, ColorMapping>,
    #[serde(default = "default_fuzziness")]
    pub default_fuzziness: f64,
    #[serde(default)]
    pub fill_nan_values: bool,
    #[serde(default = "default_fill_iterations")]
    pub fill_max_iterations: usize,
    #[serde(default = "default_neighborhood")]
    pub fill_neighborhood_size: usize,
}

impl Default for ImageProcessingParams {
    fn default() -> Self {
        Self {
            color_map: HashMap::new(),
            default_fuzziness: 10.0,
            fill_nan_values: false,
            fill_max_iterations: 100,
            fill_neighborhood_size: 1,
        }
    }
}

#[derive(Debug, Serialize, Deserialize, Clone, Default)]
pub struct ImageConfig {
    #[serde(default)]
    pub source: ImageSourceParams,
    #[serde(default)]
    pub processing: ImageProcessingParams,
}

impl ImageConfig {
    pub fn load_from_yaml<P: AsRef<Path>>(path: P) -> Result<Self> {
        let file = File::open(path).context("Failed to open config file")?;
        let config: Self = serde_yaml::from_reader(file).context("Failed to parse config file")?;
        Ok(config)
    }
}

fn default_true() -> bool {
    true
}

fn default_fuzziness() -> f64 {
    10.0
}

fn default_fill_iterations() -> usize {
    100
}

fn default_neighborhood() -> usize {
    1
}
