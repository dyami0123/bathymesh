import * as THREE from "three";
import type { Grid, GridStats } from "./types";

function getHeightColor(t: number): THREE.Color {
    const stops = [
        { t: 0.0, color: new THREE.Color("#1d4e89") },
        { t: 0.3, color: new THREE.Color("#2a9d8f") },
        { t: 0.5, color: new THREE.Color("#7cb342") },
        { t: 0.72, color: new THREE.Color("#c2a878") },
        { t: 1.0, color: new THREE.Color("#f5f5f5") },
    ];

    const clamped = THREE.MathUtils.clamp(t, 0, 1);

    for (let i = 0; i < stops.length - 1; i++) {
        const left = stops[i];
        const right = stops[i + 1];
        if (left && right && clamped >= left.t && clamped <= right.t) {
            const localT = (clamped - left.t) / (right.t - left.t || 1);
            return left.color.clone().lerp(right.color, localT);
        }
    }

    const lastStop = stops[stops.length - 1];
    return lastStop ? lastStop.color.clone() : new THREE.Color("#f5f5f5");
}

export function buildHeightColorArray(data: Grid, stats: GridStats) {
    const rows = data.length;
    const cols = data[0]?.length ?? 0;
    const colors = new Float32Array(rows * cols * 3);
    const range = Math.max(stats.max - stats.min, 1e-6);

    for (let r = 0; r < rows; r++) {
        const row = data[r];
        if (row === undefined) continue;

        for (let c = 0; c < cols; c++) {
            const index = r * cols + c;
            const value = row[c];
            if (value === undefined) continue;

            const normalized = (value - stats.min) / range;
            const color = getHeightColor(normalized);

            colors[index * 3 + 0] = color.r;
            colors[index * 3 + 1] = color.g;
            colors[index * 3 + 2] = color.b;
        }
    }

    return colors;
}
