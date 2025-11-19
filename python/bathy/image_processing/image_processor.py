"""Image to heightmap conversion utilities."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
from bathy.image_processing.color_mapper import ColorMapper
from PIL import Image
from skimage.color import rgb2lab
from sklearn.cluster import KMeans
from tqdm import tqdm

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Processes images to create heightmaps based on color mapping.

    Uses vectorized processing with scikit-image's optimized LAB color conversion
    for maximum performance. Includes tqdm progress bars for long-running operations.
    """

    def __init__(self):
        """Initialize the processor."""
        self.logger = logger

    def load_image(
        self,
        image_path: Union[str, Path],
        preserve_full_resolution: bool = True,
        max_dimension: Optional[int] = None,
    ) -> np.ndarray:
        """
        Load an image file and return as RGB array with full resolution control.

        Args:
            image_path: Path to image file
            preserve_full_resolution: If True, loads at original resolution
            max_dimension: If specified, resize image so largest dimension is this size

        Returns:
            RGB image array with shape (height, width, 3)
        """
        with tqdm(
            desc=f"Loading image {Path(image_path).name}", total=1, unit="file"
        ) as pbar:
            # Prevent PIL from automatically limiting large images
            if preserve_full_resolution:
                # Remove PIL's default size limit
                Image.MAX_IMAGE_PIXELS = None

            with Image.open(image_path) as img:
                # Log original dimensions
                self.logger.info(
                    f"Original image size: {img.size[0]}x{img.size[1]} pixels"
                )

                # Resize if max_dimension is specified
                if max_dimension is not None:
                    current_max = max(img.size)
                    if current_max > max_dimension:
                        ratio = max_dimension / current_max
                        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                        self.logger.info(
                            f"Resized to: {new_size[0]}x{new_size[1]} pixels"
                        )

                # Convert to RGB (handles RGBA, grayscale, etc.)
                rgb_img = img.convert("RGB")
                result = np.array(rgb_img)

                self.logger.info(f"Loaded array shape: {result.shape}")
                pbar.update(1)
                return result

    def process_image_to_heightmap(
        self,
        image: np.ndarray,
        color_map: Dict[str, Union[float, Dict]],
        default_fuzziness: float = 10.0,
        region: Optional[Tuple[int, int, int, int]] = None,
        fill_nan_values: bool = False,
        fill_max_iterations: int = 100,
        fill_neighborhood_size: int = 1,
    ) -> np.ndarray:
        """
        Process an image to create a heightmap based on color mapping.

        Args:
            image: RGB image array with shape (height, width, 3)
            color_map: Dictionary mapping hex colors to values/config
            default_fuzziness: Default fuzziness for color matching
            region: Optional (x_start, y_start, x_end, y_end) for sub-region
            fill_nan_values: If True, iteratively fill NaN values with neighbor averages
            fill_max_iterations: Maximum iterations for NaN filling
            fill_neighborhood_size: Neighborhood size for filling (1=3x3, 2=5x5, etc.)

        Returns:
            2D heightmap array with float values (NaN for unmatched pixels, unless filled)
        """
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(
                f"Expected RGB image with shape (H, W, 3), got {image.shape}"
            )

        # Extract region if specified
        if region is not None:
            x_start, y_start, x_end, y_end = region
            image = image[y_start:y_end, x_start:x_end]
            self.logger.info(
                f"Processing sub-region: ({x_start}, {y_start}) to ({x_end}, {y_end})"
            )

        height, width = image.shape[:2]
        self.logger.info(
            f"Processing image of size {width}x{height} with {len(color_map)} color mappings"
        )

        # Initialize color mapper
        mapper = ColorMapper(color_map, default_fuzziness)

        # Generate initial heightmap
        heightmap = self._process_vectorized_optimized(image, mapper)

        # Optionally fill NaN values
        if fill_nan_values:
            heightmap = self.fill_nan_values(
                heightmap,
                max_iterations=fill_max_iterations,
                neighborhood_size=fill_neighborhood_size,
            )

        return heightmap

    def _process_vectorized_optimized(
        self, image: np.ndarray, mapper: ColorMapper
    ) -> np.ndarray:
        """Vectorized processing using scikit-image LAB conversion."""
        height, width = image.shape[:2]

        # Create heightmap array
        heightmap = np.full((height, width), np.nan, dtype=np.float64)
        heightmap_flat = heightmap.reshape(-1)

        # Convert to LAB using scikit-image (optimized)
        with tqdm(desc="Converting to LAB", total=1, unit="step") as pbar:
            # Normalize to 0-1 for scikit-image
            image_norm = image.astype(np.float64) / 255.0
            lab_image = rgb2lab(image_norm)
            pixels_lab = lab_image.reshape(-1, 3)
            pbar.update(1)

        matched_pixels = 0

        # Process each color mapping
        with tqdm(
            total=len(mapper.color_map), desc="Processing color mappings", unit="colors"
        ) as pbar:
            for hex_color, config in mapper.color_map.items():
                target_lab = np.array(config["lab"])
                fuzziness = config["fuzziness"]
                value = config["value"]

                # Vectorized distance calculation
                distances = np.sqrt(np.sum((pixels_lab - target_lab) ** 2, axis=1))
                mask = (distances <= fuzziness) & np.isnan(heightmap_flat)

                heightmap_flat[mask] = value
                matched_pixels += np.sum(mask)
                pbar.update(1)

        match_percentage = (matched_pixels / len(heightmap_flat)) * 100
        self.logger.info(
            f"Matched {matched_pixels}/{len(heightmap_flat)} pixels ({match_percentage:.1f}%)"
        )

        return heightmap_flat.reshape(height, width)

    def fill_nan_values(
        self,
        heightmap: np.ndarray,
        max_iterations: int = 100,
        convergence_threshold: float = 1e-6,
        neighborhood_size: int = 1,
    ) -> np.ndarray:
        """
        Iteratively fill NaN values with the average of their non-NaN neighbors.

        Args:
            heightmap: 2D heightmap array with potential NaN values
            max_iterations: Maximum number of filling iterations
            convergence_threshold: Stop when change between iterations is below this
            neighborhood_size: Size of neighborhood (1 = 3x3, 2 = 5x5, etc.)

        Returns:
            Heightmap with NaN values filled
        """
        if not np.any(np.isnan(heightmap)):
            self.logger.info("No NaN values found - skipping fill operation")
            return heightmap.copy()

        # Work with a copy to preserve original
        filled_heightmap = heightmap.copy()

        initial_nan_count = np.sum(np.isnan(filled_heightmap))
        self.logger.info(
            f"Starting NaN filling: {initial_nan_count:,} NaN pixels to fill"
        )

        with tqdm(
            total=max_iterations,
            desc="Filling NaN values",
            unit="iterations",
            position=0,
        ) as pbar:
            for iteration in range(max_iterations):
                # Track changes for convergence
                old_heightmap = filled_heightmap.copy()

                # Find current NaN locations
                nan_mask = np.isnan(filled_heightmap)

                if not np.any(nan_mask):
                    self.logger.info(
                        f"All NaN values filled after {iteration} iterations"
                    )
                    break

                # Process each NaN pixel
                nan_locations = np.where(nan_mask)
                pixels_filled_this_iteration = 0

                for i, j in tqdm(
                    zip(nan_locations[0], nan_locations[1]),
                    desc="Processing NaN pixels",
                    leave=True,
                    position=1,
                ):
                    # Define neighborhood bounds
                    row_start = max(0, i - neighborhood_size)
                    row_end = min(filled_heightmap.shape[0], i + neighborhood_size + 1)
                    col_start = max(0, j - neighborhood_size)
                    col_end = min(filled_heightmap.shape[1], j + neighborhood_size + 1)

                    # Extract neighborhood
                    neighborhood = filled_heightmap[
                        row_start:row_end, col_start:col_end
                    ]

                    # Calculate mean of non-NaN neighbors
                    valid_neighbors = neighborhood[~np.isnan(neighborhood)]

                    if len(valid_neighbors) > 0:
                        filled_heightmap[i, j] = np.mean(valid_neighbors)
                        pixels_filled_this_iteration += 1

                # Check for convergence
                if pixels_filled_this_iteration == 0:
                    remaining_nans = np.sum(np.isnan(filled_heightmap))
                    if remaining_nans > 0:
                        self.logger.warning(
                            f"Convergence reached with {remaining_nans} isolated NaN pixels remaining"
                        )
                    break

                # Calculate change for convergence check
                change = np.nanmean(np.abs(filled_heightmap - old_heightmap))
                if change < convergence_threshold:
                    self.logger.info(
                        f"Converged after {iteration + 1} iterations (change: {change:.2e})"
                    )
                    break

                # Update progress
                current_nan_count = np.sum(np.isnan(filled_heightmap))
                pbar.set_postfix(
                    {
                        "NaN pixels": f"{current_nan_count:,}",
                        "Filled": f"{pixels_filled_this_iteration:,}",
                        "Change": f"{change:.2e}",
                    }
                )
                pbar.update(1)

        final_nan_count = np.sum(np.isnan(filled_heightmap))
        filled_count = initial_nan_count - final_nan_count
        fill_percentage = (
            (filled_count / initial_nan_count) * 100 if initial_nan_count > 0 else 0
        )

        self.logger.info(
            f"NaN filling complete: {filled_count:,}/{initial_nan_count:,} pixels filled ({fill_percentage:.1f}%)"
        )

        return filled_heightmap

    def process_image_file_to_heightmap(
        self,
        image_path: Union[str, Path],
        color_map: Dict[str, Union[float, Dict]],
        default_fuzziness: float = 10.0,
        region: Optional[Tuple[int, int, int, int]] = None,
        preserve_full_resolution: bool = True,
        max_dimension: Optional[int] = None,
        fill_nan_values: bool = False,
        fill_max_iterations: int = 100,
        fill_neighborhood_size: int = 1,
    ) -> np.ndarray:
        """
        Load an image file and process it to create a heightmap.

        Args:
            image_path: Path to image file
            color_map: Dictionary mapping hex colors to values/config
            default_fuzziness: Default fuzziness for color matching
            region: Optional (x_start, y_start, x_end, y_end) for sub-region
            preserve_full_resolution: If True, loads at original resolution (default)
            max_dimension: If specified, resize so largest dimension is this size
            fill_nan_values: If True, iteratively fill NaN values with neighbor averages
            fill_max_iterations: Maximum iterations for NaN filling
            fill_neighborhood_size: Neighborhood size for filling (1=3x3, 2=5x5, etc.)

        Returns:
            2D heightmap array with float values (NaN for unmatched pixels, unless filled)
        """
        image = self.load_image(image_path, preserve_full_resolution, max_dimension)
        return self.process_image_to_heightmap(
            image,
            color_map,
            default_fuzziness,
            region,
            fill_nan_values,
            fill_max_iterations,
            fill_neighborhood_size,
        )

    def get_image_info(self, image_path: Union[str, Path]) -> Dict:
        """
        Get detailed information about an image file to diagnose resolution issues.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with comprehensive image information
        """
        with Image.open(image_path) as img:
            # Get basic info
            info = {
                "file_path": str(image_path),
                "file_size_mb": Path(image_path).stat().st_size / (1024 * 1024),
                "pil_size": img.size,  # (width, height)
                "pil_mode": img.mode,
                "pil_format": img.format,
                "has_transparency": img.mode in ("RGBA", "LA", "P"),
            }

            # Load and check actual array dimensions
            rgb_img = img.convert("RGB")
            img_array = np.array(rgb_img)
            info["array_shape"] = img_array.shape
            info["array_height"] = img_array.shape[0]
            info["array_width"] = img_array.shape[1]
            info["total_pixels"] = img_array.shape[0] * img_array.shape[1]

            # Check if PIL size matches array dimensions
            pil_width, pil_height = img.size
            array_height, array_width = img_array.shape[:2]
            info["size_mismatch"] = (pil_width != array_width) or (
                pil_height != array_height
            )

            return info

    def extract_dominant_colors(
        self,
        image: np.ndarray,
        n_colors: int = 10,
        sample_ratio: float = 0.1,
        use_clustering: bool = True,
    ) -> List[Tuple[str, int]]:
        """
        Extract dominant colors from an image to help with color mapping setup.

        Args:
            image: RGB image array
            n_colors: Number of dominant colors to extract
            sample_ratio: Fraction of pixels to sample for performance
            use_clustering: Whether to use K-means clustering (requires scikit-learn)

        Returns:
            List of (hex_color, count) tuples sorted by frequency
        """

        # Sample pixels for performance
        height, width = image.shape[:2]
        n_samples = int(height * width * sample_ratio)

        # Flatten and sample with progress indication
        self.logger.info(
            f"Sampling {n_samples} pixels from {height * width} total pixels"
        )
        pixels = image.reshape(-1, 3)
        if n_samples < len(pixels):
            with tqdm(desc="Sampling pixels", total=1, unit="step") as pbar:
                indices = np.random.choice(len(pixels), n_samples, replace=False)
                pixels = pixels[indices]
                pbar.update(1)

        if use_clustering:
            # Cluster colors using K-means
            with tqdm(desc="Clustering colors", total=1, unit="step") as pbar:
                kmeans = KMeans(
                    n_clusters=min(n_colors, len(pixels)),
                    random_state=42,
                    n_init=10,  # type: ignore
                )
                kmeans.fit(pixels)
                pbar.update(1)

            # Get colors and counts
            colors = kmeans.cluster_centers_.astype(int)
            labels = kmeans.labels_

            # Count occurrences
            unique, counts = np.unique(labels, return_counts=True)  # type: ignore

            # Convert to hex and sort by frequency
            color_counts = []
            with tqdm(
                desc="Converting colors", total=len(unique), unit="colors"
            ) as pbar:
                for i, count in zip(unique, counts):
                    hex_color = (
                        f"#{colors[i][0]:02x}{colors[i][1]:02x}{colors[i][2]:02x}"
                    )
                    color_counts.append((hex_color, count))
                    pbar.update(1)
        else:
            # Simple histogram-based approach (no clustering)
            with tqdm(desc="Quantizing colors", total=1, unit="step") as pbar:
                # Quantize colors to reduce the number of unique colors
                quantized_pixels = (pixels // 32) * 32  # Group similar colors
                pbar.update(1)

            # Count unique colors
            with tqdm(desc="Counting unique colors", total=1, unit="step") as pbar:
                unique_pixels, counts = np.unique(
                    quantized_pixels, axis=0, return_counts=True
                )
                pbar.update(1)

            # Sort by frequency and take top n_colors
            sorted_indices = np.argsort(counts)[::-1][:n_colors]

            color_counts = []
            with tqdm(
                desc="Converting colors", total=len(sorted_indices), unit="colors"
            ) as pbar:
                for i in sorted_indices:
                    color = unique_pixels[i].astype(int)
                    hex_color = f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
                    color_counts.append((hex_color, counts[i]))
                    pbar.update(1)

        return sorted(color_counts, key=lambda x: x[1], reverse=True)
