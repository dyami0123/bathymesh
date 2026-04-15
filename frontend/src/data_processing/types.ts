export type NullableGrid = (number | null)[][];
export type Grid = number[][];
export type ColorMode = "height" | "image";

export type GridStats = {
    min: number;
    max: number;
};

export type SurfaceData = {
    grid: Grid;
    stats: GridStats;
    heightColors: Float32Array;
    imageColors: Float32Array | null;
};
