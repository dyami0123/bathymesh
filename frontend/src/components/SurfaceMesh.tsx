import { useEffect, useMemo, useRef } from "react";
import * as THREE from "three";
import type { Grid, GridStats } from "@/data_processing";
import { buildSurfaceGeometry } from "@/data_processing/buildSurfaceGeometry";
import { useThree } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
const SURFACE_MAX_HEIGHT = 24;

export function SurfaceMesh({
    data,
    activeColors,
    stats,
}: {
    data: Grid;
    activeColors: Float32Array;
    stats: GridStats;
}) {
    const geometry = useMemo(
        () => buildSurfaceGeometry(data, stats, SURFACE_MAX_HEIGHT),
        [data, stats]
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

    return (
        <mesh geometry={geometry} castShadow receiveShadow>
            <meshStandardMaterial
                vertexColors
                roughness={0.9}
                metalness={0.04}
                side={THREE.DoubleSide}
            />
        </mesh>
    );
}

export function CameraRig({ data, stats }: { data: Grid; stats: GridStats }) {
    const { camera } = useThree();
    const controlsRef = useRef<THREE.EventDispatcher | null>(null);

    useEffect(() => {
        const rows = data.length;
        const cols = data[0]?.length ?? 0;
        const width = Math.max(1, cols - 1);
        const depth = Math.max(1, rows - 1);
        const height = Math.max(1, SURFACE_MAX_HEIGHT);
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
    }, [camera, data, stats]);

    const size = Math.max(
        data[0]?.length ?? 1,
        data.length,
        SURFACE_MAX_HEIGHT,
        1
    );

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
