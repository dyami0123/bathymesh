import { useMemo, useEffect, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import type { MeshDataJson } from "@/client";

type MeshDisplayProps = {
    meshData: MeshDataJson;
    wireframe?: boolean;
};

export function MeshDisplay({ meshData, wireframe = false }: MeshDisplayProps) {
    const meshRef = useRef<THREE.Mesh>(null);
    const loggedOnceRef = useRef(false);

    // Build the THREE geometry from the mesh data
    const geometry = useMemo(() => {
        console.log("[MeshDisplay] Building geometry from mesh data", {
            vertexCount: meshData.vertices.length,
            triangleCount: meshData.triangles.length,
            originalWidth: meshData.original_width,
            originalHeight: meshData.original_height,
        });

        const geom = new THREE.BufferGeometry();

        // Scale vertices to align with preview heightmap coordinates
        // The mesh is generated at full resolution, but preview is at 75x56
        // So we need to scale x-y coordinates accordingly
        let vertices = new Float32Array(meshData.vertices.flat());

        if (
            meshData.original_width &&
            meshData.original_height &&
            meshData.original_width > 0 &&
            meshData.original_height > 0
        ) {
            // Scale factors to convert from original resolution to preview resolution
            // Preview uses 75x56, so we calculate scale relative to that
            const PREVIEW_WIDTH = 75;
            const PREVIEW_HEIGHT = 56;
            const xScale = PREVIEW_WIDTH / meshData.original_width;
            const yScale = PREVIEW_HEIGHT / meshData.original_height;

            console.log("[MeshDisplay] Scaling mesh coordinates", {
                xScale,
                yScale,
                originalDims: {
                    width: meshData.original_width,
                    height: meshData.original_height,
                },
                previewDims: { width: PREVIEW_WIDTH, height: PREVIEW_HEIGHT },
            });

            // Create a new Float32Array with scaled coordinates
            const scaledVertices = new Float32Array(vertices.length);
            for (let i = 0; i < vertices.length; i += 3) {
                scaledVertices[i] = vertices[i] * xScale; // x
                scaledVertices[i + 1] = vertices[i + 2]; // y
                scaledVertices[i + 2] = vertices[i + 1] * yScale; // z unchanged
            }
            vertices = scaledVertices;
        }

        const indices = new Uint32Array(meshData.triangles.flat());

        console.log("[MeshDisplay] Geometry data:", {
            verticesLength: vertices.length,
            indicesLength: indices.length,
            expectedVerticesLength: meshData.vertices.length * 3,
            expectedIndicesLength: meshData.triangles.length * 3,
        });

        geom.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
        geom.setIndex(new THREE.BufferAttribute(indices, 1));
        geom.computeVertexNormals();

        // Calculate bounds before normalization
        geom.computeBoundingBox();
        if (geom.boundingBox) {
            console.log("[MeshDisplay] Original mesh bounds:", {
                min: geom.boundingBox.min.toArray(),
                max: geom.boundingBox.max.toArray(),
            });

            // Center the mesh at origin
            const center = geom.boundingBox.getCenter(new THREE.Vector3());
            console.log("[MeshDisplay] Computed center:", center.toArray());

            // Translate geometry to center at origin
            geom.translate(-center.x, -center.y, -center.z);

            // Recalculate bounds after translation
            geom.computeBoundingBox();
            console.log("[MeshDisplay] Normalized mesh bounds:", {
                min: geom.boundingBox.min.toArray(),
                max: geom.boundingBox.max.toArray(),
            });
        }

        console.log("[MeshDisplay] Geometry built successfully");

        return geom;
    }, [meshData]);

    useEffect(() => {
        return () => {
            console.log("[MeshDisplay] Disposing geometry");
            geometry.dispose();
        };
    }, [geometry]);

    useEffect(() => {
        console.log("[MeshDisplay] Wireframe mode:", wireframe);
    }, [wireframe]);

    useFrame((state) => {
        if (meshRef.current && !loggedOnceRef.current) {
            loggedOnceRef.current = true;
            console.log("[MeshDisplay] Mesh position in scene:", {
                position: meshRef.current.position.toArray(),
                visible: meshRef.current.visible,
                scale: meshRef.current.scale.toArray(),
                castShadow: meshRef.current.castShadow,
                receiveShadow: meshRef.current.receiveShadow,
                geometry: {
                    boundingBox: meshRef.current.geometry.boundingBox?.toJSON(),
                },
                cameraPosition: state.camera.position.toArray(),
                cameraLookAt: state.camera
                    .getWorldDirection(new THREE.Vector3())
                    .toArray(),
            });
        }
    });

    return (
        <mesh ref={meshRef} geometry={geometry} castShadow receiveShadow>
            <meshStandardMaterial
                color="#8b7355"
                roughness={0.7}
                metalness={0.1}
                side={THREE.DoubleSide}
                wireframe={wireframe}
            />
        </mesh>
    );
}
