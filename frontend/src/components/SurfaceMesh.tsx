import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import type { Grid, GridStats } from "@/data_processing";
import {
    buildSurfaceGeometry,
    type HeightMode,
} from "@/data_processing/buildSurfaceGeometry";
import { useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import type { ThreeEvent } from "@react-three/fiber";
const SURFACE_NORMALIZED_HEIGHT = 24;

export function SurfaceMesh({
    data,
    activeColors,
    stats,
    onPickColor,
    isPickingActive = false,
    onHover,
    onHoverEnd,
    heightMode = "normalized",
}: {
    data: Grid;
    activeColors: Float32Array;
    stats: GridStats;
    onPickColor?: (row: number, col: number) => void;
    isPickingActive?: boolean;
    onHover?: (
        row: number,
        col: number,
        clientX: number,
        clientY: number
    ) => void;
    onHoverEnd?: () => void;
    heightMode?: HeightMode;
}) {
    const geometry = useMemo(
        () =>
            buildSurfaceGeometry(
                data,
                stats,
                SURFACE_NORMALIZED_HEIGHT,
                heightMode
            ),
        [data, stats, heightMode]
    );

    useEffect(() => {
        const colorAttr = new THREE.BufferAttribute(activeColors, 3);
        geometry.setAttribute("color", colorAttr);
        const colorAttribute = geometry.attributes.color;
        if (colorAttribute) {
            colorAttribute.needsUpdate = true;
        }

        return () => {
            geometry.deleteAttribute("color");
        };
    }, [activeColors, geometry]);

    useEffect(() => {
        return () => {
            geometry.dispose();
        };
    }, [geometry]);

    const resolveGridCoords = (
        event: ThreeEvent<MouseEvent> | ThreeEvent<PointerEvent>
    ): { row: number; col: number } | null => {
        const face = event.face;
        if (!face) return null;

        const positionAttr = geometry.attributes
            .position as THREE.BufferAttribute;
        const candidates = [face.a, face.b, face.c];
        const point = event.point;
        const worldMatrix = event.object.matrixWorld;

        let closestIndex = candidates[0]!;
        let closestDist = Infinity;
        const tempVec = new THREE.Vector3();

        for (const idx of candidates) {
            tempVec.fromBufferAttribute(positionAttr, idx);
            tempVec.applyMatrix4(worldMatrix);
            const dist = tempVec.distanceTo(point);
            if (dist < closestDist) {
                closestDist = dist;
                closestIndex = idx;
            }
        }

        const cols = data[0]?.length ?? 0;
        const row = Math.floor(closestIndex / cols);
        const col = closestIndex % cols;

        if (row >= 0 && row < data.length && col >= 0 && col < cols) {
            return { row, col };
        }
        return null;
    };

    const handleClick = (event: ThreeEvent<MouseEvent>) => {
        console.debug("[color-pick] SurfaceMesh clicked", {
            hasCallback: !!onPickColor,
            face: event.face
                ? { a: event.face.a, b: event.face.b, c: event.face.c }
                : null,
            point: event.point.toArray(),
        });
        if (!onPickColor) return;

        const coords = resolveGridCoords(event);
        if (!coords) return;

        console.debug("[color-pick] resolved grid coords", {
            row: coords.row,
            col: coords.col,
            gridRows: data.length,
            gridCols: data[0]?.length ?? 0,
        });

        event.stopPropagation();
        onPickColor(coords.row, coords.col);
    };

    const handlePointerMove = (event: ThreeEvent<PointerEvent>) => {
        if (!isPickingActive || !onHover) return;
        const coords = resolveGridCoords(event);
        if (coords) {
            onHover(
                coords.row,
                coords.col,
                event.nativeEvent.clientX,
                event.nativeEvent.clientY
            );
        }
    };

    const handlePointerLeave = () => {
        if (isPickingActive) {
            onHoverEnd?.();
        }
    };

    return (
        <mesh
            geometry={geometry}
            castShadow
            receiveShadow
            onClick={handleClick}
            onPointerMove={handlePointerMove}
            onPointerLeave={handlePointerLeave}
        >
            <meshStandardMaterial
                vertexColors
                roughness={0.9}
                metalness={0.04}
                side={THREE.DoubleSide}
            />
        </mesh>
    );
}

export function CameraRig({
    data,
    stats,
    isFirstLoad = false,
    heightMode = "normalized",
}: {
    data: Grid;
    stats: GridStats;
    isFirstLoad?: boolean;
    heightMode?: HeightMode;
}) {
    const { camera } = useThree();
    const controlsRef = useRef<THREE.EventDispatcher | null>(null);
    const cameraInitializedRef = useRef(false);

    useEffect(() => {
        // Only initialize camera position on first load
        if (!isFirstLoad && cameraInitializedRef.current) {
            return;
        }

        const rows = data.length;
        const cols = data[0]?.length ?? 0;
        const width = Math.max(1, cols - 1);
        const depth = Math.max(1, rows - 1);
        const valueRange = Math.max(stats.max - stats.min, 1e-6);
        const height =
            heightMode === "normalized"
                ? Math.max(1, SURFACE_NORMALIZED_HEIGHT)
                : Math.max(1, valueRange);
        const size = Math.max(width, depth, height);

        camera.position.set(size * 0.95, size * 0.75, size * 0.95);
        camera.near = Math.max(0.1, size / 1000);
        camera.far = size * 20;
        camera.lookAt(0, 0, 0);
        camera.updateProjectionMatrix();

        const controls = controlsRef.current as
            | (THREE.EventDispatcher & {
                  target?: THREE.Vector3;
                  update?: () => void;
              })
            | null;

        if (controls?.target) {
            controls.target.set(0, 0, 0);
            controls.update?.();
        }

        cameraInitializedRef.current = true;
    }, [isFirstLoad, camera, data, stats, heightMode]);

    const valueRange = Math.max(stats.max - stats.min, 1e-6);
    const height =
        heightMode === "normalized"
            ? Math.max(1, SURFACE_NORMALIZED_HEIGHT)
            : Math.max(1, valueRange);
    const size = Math.max(data[0]?.length ?? 1, data.length, height, 1);

    return (
        <OrbitControls
            ref={controlsRef as any}
            enablePan={true}
            enableDamping
            dampingFactor={0.08}
            minDistance={size * 0.35}
            maxDistance={size * 6}
            rotateSpeed={0.8}
            zoomSpeed={0.9}
        />
    );
}
