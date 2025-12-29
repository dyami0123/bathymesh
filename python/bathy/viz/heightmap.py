from pathlib import Path
from typing import Union

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def heightmap_plot(
    data: np.ndarray, save_path: Union[Path, None]
) -> tuple[Figure, Axes]:

    fig, ax = plt.subplots(figsize=(10, 8))
    plt.imshow(data, cmap="viridis", interpolation="nearest")
    plt.colorbar(label="Height")
    plt.title("Generated Heightmap")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.tight_layout()

    if save_path is not None:
        plt.savefig(save_path)

    return fig, ax
