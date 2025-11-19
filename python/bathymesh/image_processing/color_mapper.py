"""Image to heightmap conversion utilities."""

import logging
from collections import OrderedDict
from typing import Dict, Optional, Tuple, Union

import numpy as np

logger = logging.getLogger(__name__)


class ColorMapper:
    """
    Utility for mapping colors to values with fuzziness control.

    Fuzziness represents Delta E distance in LAB color space:
    - Delta E 0-1: Virtually identical (imperceptible)
    - Delta E 1-3: Very slight difference (barely noticeable)
    - Delta E 3-6: Moderate difference (clearly noticeable)
    - Delta E 6-12: Large difference (very noticeable)
    - Delta E 12+: Huge difference (completely different)

    Recommended fuzziness values:
    - 2-5: Clean digital images, precise matching
    - 8-15: Typical photos/scanned maps (default range)
    - 15-25: Noisy/low-quality images
    - 25-40: Broad color categories
    """

    def __init__(
        self, color_map: Dict[str, Union[float, Dict]], default_fuzziness: float = 10.0
    ):
        """
        Initialize color mapper.

        Args:
            color_map: Dictionary mapping hex colors to target values.
                      Values can be:
                      - float: Simple value with default fuzziness
                      - dict: {'value': float, 'fuzziness': float}
            default_fuzziness: Default fuzziness value (Delta E) when not specified.
                             Typical values: 2-5 (strict), 8-15 (moderate), 15-25 (loose)
        """
        self.color_map = OrderedDict()  # Preserve order for priority
        self.default_fuzziness = default_fuzziness

        for hex_color, config in color_map.items():
            rgb = self._hex_to_rgb(hex_color)
            lab = self._rgb_to_lab(rgb)

            if isinstance(config, (int, float)):
                value = float(config)
                fuzziness = default_fuzziness
            else:
                value = float(config["value"])
                fuzziness = float(config.get("fuzziness", default_fuzziness))

            self.color_map[hex_color] = {
                "value": value,
                "fuzziness": fuzziness,
                "rgb": rgb,
                "lab": lab,
            }

    @staticmethod
    def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:
            raise ValueError(f"Invalid hex color: {hex_color}")
        return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore

    @staticmethod
    def _rgb_to_lab(rgb: Tuple[int, int, int]) -> Tuple[float, float, float]:
        """
        Convert RGB to LAB color space for perceptual color distance.

        This is a simplified conversion. For production use, consider using
        scikit-image's rgb2lab function for more accuracy.
        """
        r, g, b = [x / 255.0 for x in rgb]

        # Convert to XYZ (simplified sRGB)
        r = ((r + 0.055) / 1.055) ** 2.4 if r > 0.04045 else r / 12.92
        g = ((g + 0.055) / 1.055) ** 2.4 if g > 0.04045 else g / 12.92
        b = ((b + 0.055) / 1.055) ** 2.4 if b > 0.04045 else b / 12.92

        # Observer = 2°, Illuminant = D65
        x = r * 0.4124 + g * 0.3576 + b * 0.1805
        y = r * 0.2126 + g * 0.7152 + b * 0.0722
        z = r * 0.0193 + g * 0.1192 + b * 0.9505

        # Normalize for D65
        x /= 0.95047
        y /= 1.00000
        z /= 1.08883

        # Convert to LAB
        x = x ** (1 / 3) if x > 0.008856 else (7.787 * x + 16 / 116)
        y = y ** (1 / 3) if y > 0.008856 else (7.787 * y + 16 / 116)
        z = z ** (1 / 3) if z > 0.008856 else (7.787 * z + 16 / 116)

        L = 116 * y - 16
        a = 500 * (x - y)
        b = 200 * (y - z)

        return (L, a, b)

    @staticmethod
    def _color_distance_lab(
        lab1: Tuple[float, float, float], lab2: Tuple[float, float, float]
    ) -> float:
        """Calculate perceptual color distance in LAB space (Delta E)."""
        dL = lab1[0] - lab2[0]
        da = lab1[1] - lab2[1]
        db = lab1[2] - lab2[2]
        return np.sqrt(dL**2 + da**2 + db**2)

    def map_pixel_to_value(self, rgb: Tuple[int, int, int]) -> Optional[float]:
        """
        Map a single RGB pixel to a value based on the color mapping.

        Args:
            rgb: RGB tuple (0-255)

        Returns:
            Mapped value or None if no match found
        """
        pixel_lab = self._rgb_to_lab(rgb)

        # Check colors in order (first match wins if multiple matches)
        for hex_color, config in self.color_map.items():
            distance = self._color_distance_lab(pixel_lab, config["lab"])
            if distance <= config["fuzziness"]:
                return config["value"]

        return None
