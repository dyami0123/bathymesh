import * as THREE from "three";
import type { Grid, GridStats } from "./types";

export function buildSurfaceGeometry(
    data: Grid,
    stats: GridStats,
    max_height: number
) {
    const rows = data.length;
    const cols = data[0]?.length ?? 0;
    const width = Math.max(1, cols - 1);
    const depth = Math.max(1, rows - 1);
    const geometry = new THREE.PlaneGeometry(width, depth, cols - 1, rows - 1);
    const positionAttr = geometry.attributes.position as THREE.BufferAttribute;

    const valueRange = Math.max(stats.max - stats.min, 1e-6);
    const zScale = max_height / valueRange;

    for (let r = 0; r < rows; r++) {
        const row = data[r];
        if (!row) continue;
        for (let c = 0; c < cols; c++) {
            const index = r * cols + c;
            const value = row[c];
            if (value !== undefined) {
                positionAttr.setZ(index, (value - stats.min) * zScale);
            }
        }
    }

    positionAttr.needsUpdate = true;
    geometry.computeVertexNormals();
    geometry.center();
    geometry.rotateX(-Math.PI / 2);

    return geometry;
}
