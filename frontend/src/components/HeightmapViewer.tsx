import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { useProject } from "@/state/projectContext";
import {
    getProjectHeightmapApiHeightmapProjectIdGet,
    getProjectImageApiImageProjectIdGet,
} from "@/client";
import type { SurfaceData, ColorMode } from "@/data_processing";
import { buildHeightColorArray } from "@/data_processing/heightColormap";
import { Spinner } from "./Spinner";
import { getImageColorsFromAPIResult } from "@/data_processing/imageProcessing";
import { JobSubmitButton } from "./jobSubmitter";
import { SurfaceMesh, CameraRig } from "./SurfaceMesh";
import {
    // calculateProjectContoursApiContoursProjectIdPost,
    calculateProjectHeightmapApiHeightmapProjectIdPost,
} from "@/client";
import { blockingApiCall } from "@/blockingApiCall";

const PREVIEW_DIM = 150;

export function HeightmapViewer() {
    const project = useProject();
    const [surfaceData, setSurfaceData] = useState<SurfaceData | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [colorMode, setColorMode] = useState<ColorMode>("height");
    const hasInitialDataRef = useRef(false);

    const loadData = useCallback(async () => {
        const isFirstLoad = !hasInitialDataRef.current;

        if (isFirstLoad) {
            setLoading(true);
            blockingApiCall({
                endpoint: calculateProjectHeightmapApiHeightmapProjectIdPost,
                project_id: project.project_id,
                body: { is_preview: true, max_dimension_override: PREVIEW_DIM },
            });
        } else {
            setRefreshing(true);
        }
        setError(null);

        try {
            const [heightmapResult, imageResult] = await Promise.allSettled([
                // # TODO: update to new API.
                getProjectHeightmapApiHeightmapProjectIdGet({
                    path: { project_id: project.project_id },
                    throwOnError: true,
                    query: { is_preview: true },
                }),
                getProjectImageApiImageProjectIdGet({
                    path: { project_id: project.project_id },
                    throwOnError: true,
                    query: { max_dimension: PREVIEW_DIM },
                }),
            ]);

            if (heightmapResult.status === "rejected") {
                throw heightmapResult.reason;
            }

            const raw = heightmapResult.value.data?.data;
            if (!raw?.length || !raw[0]?.length) {
                throw new Error(
                    "No heightmap data available. Please calculate one first."
                );
            }

            // const filled = fillNulls(sampled, fullStats.mean);
            const filled = raw.map((row) =>
                row.map((v) => (v == null || Number.isNaN(v) ? 0 : v))
            );

            const min_val = filled.reduce(
                (min, row) =>
                    Math.min(
                        min,
                        ...row.map((v) =>
                            v == null || Number.isNaN(v) ? Infinity : v
                        )
                    ),
                Infinity
            );

            const max_val = filled.reduce(
                (max, row) =>
                    Math.max(
                        max,
                        ...row.map((v) =>
                            v == null || Number.isNaN(v) ? -Infinity : v
                        )
                    ),
                -Infinity
            );

            const stats = {
                min: min_val,
                max: max_val,
            };
            const heightColors = buildHeightColorArray(filled, stats);

            let imageColors: Float32Array | null =
                await getImageColorsFromAPIResult(filled, imageResult);

            const nextSurface: SurfaceData = {
                grid: filled,
                stats: stats,
                heightColors,
                imageColors,
            };

            setSurfaceData(nextSurface);
            setColorMode((prev) =>
                prev === "image" && !nextSurface.imageColors ? "height" : prev
            );
        } catch (err) {
            const message =
                err instanceof Error
                    ? err.message
                    : "Failed to fetch surface data";
            setError(message);
        } finally {
            hasInitialDataRef.current = true;
            setLoading(false);
            setRefreshing(false);
        }
    }, [project.project_id]);

    useEffect(() => {
        void loadData();
    }, [loadData]);

    const activeColors = useMemo(() => {
        if (!surfaceData) return null;
        if (colorMode === "image" && surfaceData.imageColors) {
            return surfaceData.imageColors;
        }
        return surfaceData.heightColors;
    }, [colorMode, surfaceData]);

    let mainCanvas = null;

    if (loading && !surfaceData) {
        mainCanvas = (
            <div className="flex h-[70vh] w-full items-center justify-center bg-white">
                <div className="flex items-center gap-3 text-sm text-gray-600">
                    <Spinner />
                    <span>Loading surface...</span>
                </div>
            </div>
        );
    } else if (!surfaceData || !activeColors) {
        mainCanvas = (
            <div className="flex h-[70vh] w-full items-center justify-center bg-white">
                <p className="text-sm text-red-600">
                    {error ?? "No surface data available."}
                </p>
            </div>
        );
    } else {
        mainCanvas = (
            <div className="relative h-[70vh] w-full overflow-hidden rounded-lg bg-white">
                <div className="absolute left-4 top-4 z-10 flex items-center gap-2 rounded-full bg-white/92 p-1 shadow-lg backdrop-blur">
                    <button
                        type="button"
                        onClick={() => setColorMode("height")}
                        className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                            colorMode === "height"
                                ? "bg-gray-900 text-white"
                                : "bg-transparent text-gray-700 hover:bg-gray-100"
                        }`}
                    >
                        Height
                    </button>

                    <button
                        type="button"
                        onClick={() => setColorMode("image")}
                        disabled={!surfaceData.imageColors}
                        className={`rounded-full px-3 py-1.5 text-sm font-medium transition ${
                            colorMode === "image"
                                ? "bg-gray-900 text-white"
                                : "bg-transparent text-gray-700 hover:bg-gray-100"
                        } disabled:cursor-not-allowed disabled:opacity-45`}
                    >
                        Image
                    </button>

                    <div className="mx-1 h-5 w-px bg-gray-200" />

                    <button
                        type="button"
                        onClick={() => void loadData()}
                        disabled={refreshing}
                        className="flex items-center gap-2 rounded-full px-3 py-1.5 text-sm font-medium text-gray-700 transition hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-60"
                    >
                        {refreshing ? <Spinner /> : null}
                        <span>{refreshing ? "Refreshing" : "Refresh"}</span>
                    </button>
                </div>

                {error ? (
                    <div className="absolute bottom-4 left-4 z-10 rounded-full bg-red-50 px-3 py-1.5 text-xs font-medium text-red-600 shadow-sm">
                        {error}
                    </div>
                ) : null}

                <Canvas shadows dpr={[1, 2]} camera={{ fov: 45 }}>
                    <color attach="background" args={["#ffffff"]} />
                    <ambientLight intensity={0.55} />
                    <directionalLight
                        position={[30, 40, 20]}
                        intensity={1.25}
                        castShadow
                    />
                    <directionalLight
                        position={[-20, 10, -20]}
                        intensity={0.35}
                    />

                    <SurfaceMesh
                        data={surfaceData.grid}
                        stats={surfaceData.stats}
                        activeColors={activeColors}
                    />
                    <CameraRig
                        data={surfaceData.grid}
                        stats={surfaceData.stats}
                    />
                </Canvas>
            </div>
        );
    }
    return (
        <div>
            {mainCanvas}
            <p>TEST</p>
            <JobSubmitButton
                endpoints={{
                    calculate_heightmap:
                        calculateProjectHeightmapApiHeightmapProjectIdPost,
                    // generate_mesh: calculateProjectMeshApiMeshProjectIdPost,
                }}
                body={{ is_preview: true, max_dimension_override: PREVIEW_DIM }}
            />
        </div>
    );
}
