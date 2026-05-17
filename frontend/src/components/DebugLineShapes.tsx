import { useMemo } from "react";
import { Line } from "@react-three/drei";
import type { GridStats } from "@/data_processing";

const NORMALIZED_SCENE_HEIGHT = 24;

type Point3 = [number, number, number];

type DebugLineShapesProps = {
    rows: number;
    cols: number;
    stats: GridStats;
    heightMode: "normalized" | "absolute";
};

function buildSpinePath(width: number, depth: number, y: number): Point3[] {
    const count = 18;
    const startX = -width / 2;
    const stepX = width / Math.max(1, count - 1);
    const amp = depth * 0.28;
    const out: Point3[] = [];

    for (let idx = 0; idx < count; idx += 1) {
        const x = startX + idx * stepX;
        const t = idx / Math.max(1, count - 1);
        const z = Math.sin(t * Math.PI * 3) * amp;
        out.push([x, y, z]);
    }

    return out;
}

function buildDiamondRings(
    width: number,
    depth: number,
    y: number
): Point3[][] {
    const ringCount = 3;
    const rings: Point3[][] = [];

    for (let ringIndex = 1; ringIndex <= ringCount; ringIndex += 1) {
        const scale = ringIndex / (ringCount + 1);
        const halfW = (width / 2) * scale;
        const halfD = (depth / 2) * scale;

        rings.push([
            [0, y, -halfD],
            [halfW, y, 0],
            [0, y, halfD],
            [-halfW, y, 0],
            [0, y, -halfD],
        ]);
    }

    return rings;
}

export function DebugLineShapes({
    rows,
    cols,
    stats,
    heightMode,
}: DebugLineShapesProps) {
    const { frame, diagonals, spine, rings } = useMemo(() => {
        const width = Math.max(1, cols - 1);
        const depth = Math.max(1, rows - 1);
        const valueRange = Math.max(stats.max - stats.min, 1e-6);
        const meshHeight =
            heightMode === "normalized" ? NORMALIZED_SCENE_HEIGHT : valueRange;
        const y = meshHeight + Math.max(0.6, meshHeight * 0.04);

        const halfW = width / 2;
        const halfD = depth / 2;

        const framePoints: Point3[] = [
            [-halfW, y, -halfD],
            [halfW, y, -halfD],
            [halfW, y, halfD],
            [-halfW, y, halfD],
            [-halfW, y, -halfD],
        ];

        const diagonalPoints: Point3[] = [
            [-halfW, y, -halfD],
            [halfW, y, halfD],
            [halfW, y, -halfD],
            [-halfW, y, halfD],
        ];

        return {
            frame: framePoints,
            diagonals: diagonalPoints,
            spine: buildSpinePath(width, depth, y),
            rings: buildDiamondRings(width, depth, y),
        };
    }, [cols, heightMode, rows, stats.max, stats.min]);

    return (
        <group name="debug-line-shapes">
            <Line points={frame} color="#0ea5e9" lineWidth={1.5} />
            <Line points={diagonals} color="#f97316" lineWidth={1.25} />
            <Line points={spine} color="#10b981" lineWidth={1.5} />

            {rings.map((points, index) => (
                <Line
                    key={`debug-ring-${index}`}
                    points={points}
                    color="#a855f7"
                    lineWidth={1}
                    opacity={0.72}
                    transparent
                />
            ))}
        </group>
    );
}
