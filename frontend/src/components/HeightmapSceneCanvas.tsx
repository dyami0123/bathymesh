import { Canvas } from "@react-three/fiber";
import type { SurfaceData } from "@/data_processing";
import type { HeightMode } from "@/data_processing/buildSurfaceGeometry";
import { SurfaceMesh, CameraRig } from "./SurfaceMesh";
import { DebugLineShapes } from "./DebugLineShapes";

type HeightmapSceneCanvasProps = {
    surfaceData: SurfaceData;
    activeColors: Float32Array;
    isPickingColor: boolean;
    isFirstLoad: boolean;
    heightMode: HeightMode;
    showDebugLines?: boolean;
    onPickColor: (row: number, col: number) => void;
    onHover: (
        row: number,
        col: number,
        clientX: number,
        clientY: number
    ) => void;
    onHoverEnd: () => void;
};

export function HeightmapSceneCanvas({
    surfaceData,
    activeColors,
    isPickingColor,
    isFirstLoad,
    heightMode,
    showDebugLines = false,
    onPickColor,
    onHover,
    onHoverEnd,
}: HeightmapSceneCanvasProps) {
    return (
        <Canvas shadows dpr={[1, 2]} camera={{ fov: 45 }}>
            <color attach="background" args={["#ffffff"]} />
            <ambientLight intensity={0.55} />
            <directionalLight
                position={[30, 40, 20]}
                intensity={1.25}
                castShadow
            />
            <directionalLight position={[-20, 10, -20]} intensity={0.35} />

            <SurfaceMesh
                data={surfaceData.grid}
                stats={surfaceData.stats}
                activeColors={activeColors}
                onPickColor={onPickColor}
                isPickingActive={isPickingColor}
                onHover={onHover}
                onHoverEnd={onHoverEnd}
                heightMode={heightMode}
            />

            {showDebugLines ? (
                <DebugLineShapes
                    rows={surfaceData.grid.length}
                    cols={surfaceData.grid[0]?.length ?? 0}
                    stats={surfaceData.stats}
                    heightMode={heightMode}
                />
            ) : null}

            <CameraRig
                data={surfaceData.grid}
                stats={surfaceData.stats}
                isFirstLoad={isFirstLoad}
                heightMode={heightMode}
            />
        </Canvas>
    );
}
