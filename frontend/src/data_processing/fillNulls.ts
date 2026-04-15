import type { Grid, NullableGrid } from "./types";

export function fillNulls(data: NullableGrid, fallback: number): Grid {
    return data.map((row) =>
        row.map((v) => (v == null || Number.isNaN(v) ? fallback : v))
    );
}
