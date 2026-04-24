import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { useProject } from "@/state/projectContext";
import { useViewer, useViewerDispatch } from "@/state/viewerContext";
import {
    useColorPicker,
    useColorPickerDispatch,
} from "@/state/colorPickerContext";
import {
    getProjectHeightmapApiHeightmapProjectIdGet,
    getProjectImageApiImageProjectIdGet,
} from "@/client";
import type { SurfaceData, ColorMode } from "@/data_processing";
import { buildHeightColorArray } from "@/data_processing/heightColormap";
import { Spinner } from "./Spinner";
import { getImageColorsFromBlob } from "@/data_processing/imageProcessing";
import { JobSubmitButton } from "./jobSubmitter";
import { SurfaceMesh, CameraRig } from "./SurfaceMesh";
import {
    // calculateProjectContoursApiContoursProjectIdPost,
    calculateProjectHeightmapApiHeightmapProjectIdPost,
} from "@/client";
import { blockingApiCall } from "@/blockingApiCall";
import { cn } from "@/lib/cn";
import { button, badge } from "@/components/ui/styles";

import type { ImageData, HeightmapDataJson } from "@/client";

export const PREVIEW_DIM = 150;

type ActiveImagePayload = ImageData | Blob | File | null;

function normalizeImagePayload(payload: ActiveImagePayload): ImageData | null {
    if (!payload) {
        return null;
    }

    if (payload instanceof Blob || payload instanceof File) {
        const mimeType = payload.type;
        const validType =
            mimeType === "image/png" ||
            mimeType === "image/jpeg" ||
            mimeType === "image/tiff"
                ? mimeType
                : "image/png";

        return {
            data: payload,
            type: validType,
        };
    }

    return payload;
}

export function HeightmapViewer() {
    const project = useProject();
    const {
        activeImageData,
        activeHeightmapData,
        refreshSignal,
        isLoading: loading,
    } = useViewer();
    const viewerDispatch = useViewerDispatch();
    const { isPickingColor } = useColorPicker();
    const colorPickerDispatch = useColorPickerDispatch();

    const setLoading = useCallback(
        (value: boolean) => viewerDispatch({ type: "set_loading", value }),
        [viewerDispatch]
    );

    const setActiveImageData = useCallback(
        (data: ImageData) => viewerDispatch({ type: "set_image", data }),
        [viewerDispatch]
    );

    const setActiveHeightmapData = useCallback(
        (data: HeightmapDataJson) =>
            viewerDispatch({ type: "set_heightmap", data }),
        [viewerDispatch]
    );

    const [surfaceData, setSurfaceData] = useState<SurfaceData | null>(null);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [colorMode, setColorMode] = useState<ColorMode>("height");

    const hasInitialDataRef = useRef(false);
    const activeImageDataRef = useRef<ActiveImagePayload>(activeImageData);
    const activeHeightmapDataRef = useRef<HeightmapDataJson | null>(
        activeHeightmapData
    );

    useEffect(() => {
        activeImageDataRef.current = activeImageData;
    }, [activeImageData]);

    useEffect(() => {
        activeHeightmapDataRef.current = activeHeightmapData;
    }, [activeHeightmapData]);

    const loadData = useCallback(
        async (forceRefresh = false) => {
            const isFirstLoad = !hasInitialDataRef.current;

            let resolvedImageData = normalizeImagePayload(
                activeImageDataRef.current
            );
            let resolvedHeightmapData = activeHeightmapDataRef.current;

            if (forceRefresh) {
                resolvedImageData = null;
                resolvedHeightmapData = null;
            }

            if (isFirstLoad) {
                setLoading(true);
                const existingHeightmapResult =
                    await getProjectHeightmapApiHeightmapProjectIdGet({
                        path: { project_id: project.project_id },
                        throwOnError: true,
                        query: { is_preview: true },
                    });

                if (!existingHeightmapResult.data?.data) {
                    console.log(
                        "No existing heightmap data, calculating preview heightmap..."
                    );
                    await blockingApiCall({
                        endpoint:
                            calculateProjectHeightmapApiHeightmapProjectIdPost,
                        project_id: project.project_id,
                        body: {
                            is_preview: true,
                            max_dimension_override: PREVIEW_DIM,
                        },
                    });

                    const heightmapDataResult =
                        await getProjectHeightmapApiHeightmapProjectIdGet({
                            path: { project_id: project.project_id },
                            throwOnError: true,
                            query: { is_preview: true },
                        });
                    if (!heightmapDataResult.data?.data) {
                        throw new Error(
                            "Failed to load heightmap data after calculation. Please refresh and try again."
                        );
                    }
                    resolvedHeightmapData =
                        heightmapDataResult.data as HeightmapDataJson;
                } else {
                    console.log(
                        "Existing heightmap data found, using it for preview."
                    );
                    resolvedHeightmapData =
                        existingHeightmapResult.data as HeightmapDataJson;
                }
                activeHeightmapDataRef.current = resolvedHeightmapData;
                setActiveHeightmapData(resolvedHeightmapData);
            } else {
                setRefreshing(true);
            }
            setError(null);

            try {
                if (!resolvedImageData) {
                    console.log("No image data, fetching preview image...");
                    try {
                        const imageResult =
                            await getProjectImageApiImageProjectIdGet({
                                path: { project_id: project.project_id },
                                throwOnError: true,
                                query: { max_dimension: PREVIEW_DIM },
                            });

                        const normalizedImage = normalizeImagePayload(
                            imageResult.data as ActiveImagePayload
                        );
                        if (normalizedImage) {
                            resolvedImageData = normalizedImage;
                            activeImageDataRef.current = normalizedImage;
                            setActiveImageData(normalizedImage);
                        }
                    } catch {
                        console.info(
                            "Preview image is unavailable; continuing with height-based colors only."
                        );
                    }
                }

                if (!resolvedHeightmapData) {
                    console.log(
                        "No heightmap data, calculating preview heightmap..."
                    );
                    const heightmapResult =
                        await getProjectHeightmapApiHeightmapProjectIdGet({
                            path: { project_id: project.project_id },
                            throwOnError: true,
                            query: { is_preview: true },
                        });

                    if (!heightmapResult.data) {
                        throw new Error("No image data available.");
                    }

                    resolvedHeightmapData =
                        heightmapResult.data as HeightmapDataJson;
                    activeHeightmapDataRef.current = resolvedHeightmapData;
                    setActiveHeightmapData(resolvedHeightmapData);
                }

                const raw = resolvedHeightmapData?.data;
                if (!raw?.length || !raw[0]?.length) {
                    throw new Error(
                        "No heightmap data available. Please calculate one first."
                    );
                }

                // const filled = fillNulls(sampled, fullStats.mean);
                const filled = raw.map((row) =>
                    row.map((v) => (v == null || Number.isNaN(v) ? 0 : v))
                );

                // TODO: move to helper function? may be used elsewhere.
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
                let imageColors: Float32Array | null = null;
                if (resolvedImageData) {
                    imageColors = await getImageColorsFromBlob(
                        filled,
                        resolvedImageData
                    );
                } else {
                    console.warn(
                        "No active image data available, skipping image color extraction."
                    );
                }

                const nextSurface: SurfaceData = {
                    grid: filled,
                    stats: stats,
                    heightColors,
                    imageColors,
                };

                setSurfaceData(nextSurface);
                setColorMode((prev) =>
                    prev === "image" && !nextSurface.imageColors
                        ? "height"
                        : prev
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
        },
        [project.project_id, setActiveHeightmapData, setActiveImageData]
    );

    useEffect(() => {
        void loadData(false);
    }, [project.project_id, loadData]);

    useEffect(() => {
        if (!hasInitialDataRef.current || refreshSignal === 0) {
            return;
        }
        void loadData(true);
    }, [refreshSignal, loadData]);

    const activeColors = useMemo(() => {
        if (!surfaceData) return null;
        if (colorMode === "image" && surfaceData.imageColors) {
            return surfaceData.imageColors;
        }
        return surfaceData.heightColors;
    }, [colorMode, surfaceData]);

    const handlePickColor = useCallback(
        (row: number, col: number) => {
            console.debug("[color-pick] handlePickColor", {
                row,
                col,
                hasImageColors: !!surfaceData?.imageColors,
                imageColorsLength: surfaceData?.imageColors?.length,
            });
            if (!surfaceData?.imageColors) return;
            const cols = surfaceData.grid[0]?.length ?? 0;
            const idx = (row * cols + col) * 3;
            const r = Math.round((surfaceData.imageColors[idx + 0] ?? 0) * 255);
            const g = Math.round((surfaceData.imageColors[idx + 1] ?? 0) * 255);
            const b = Math.round((surfaceData.imageColors[idx + 2] ?? 0) * 255);
            const hex =
                "#" +
                [r, g, b].map((c) => c.toString(16).padStart(2, "0")).join("");
            console.debug("[color-pick] resolved color", { idx, r, g, b, hex });
            colorPickerDispatch({ type: "pick_color", hex });
        },
        [colorPickerDispatch, surfaceData]
    );

    const [hoverInfo, setHoverInfo] = useState<{
        color: string;
        x: number;
        y: number;
    } | null>(null);

    const resolveHexAt = useCallback(
        (row: number, col: number): string | null => {
            if (!surfaceData?.imageColors) return null;
            const cols = surfaceData.grid[0]?.length ?? 0;
            const idx = (row * cols + col) * 3;
            const r = Math.round((surfaceData.imageColors[idx] ?? 0) * 255);
            const g = Math.round((surfaceData.imageColors[idx + 1] ?? 0) * 255);
            const b = Math.round((surfaceData.imageColors[idx + 2] ?? 0) * 255);
            return (
                "#" +
                [r, g, b].map((c) => c.toString(16).padStart(2, "0")).join("")
            );
        },
        [surfaceData]
    );

    const handleHover = useCallback(
        (row: number, col: number, clientX: number, clientY: number) => {
            const hex = resolveHexAt(row, col);
            if (hex) {
                setHoverInfo({ color: hex, x: clientX, y: clientY });
            }
        },
        [resolveHexAt]
    );

    const handleHoverEnd = useCallback(() => setHoverInfo(null), []);

    useEffect(() => {
        if (!isPickingColor) {
            setHoverInfo(null);
        }
    }, [isPickingColor]);

    let mainCanvas = null;

    if (loading) {
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
            <div
                className="relative h-[70vh] w-full overflow-hidden rounded-lg bg-white"
                style={isPickingColor ? { cursor: "crosshair" } : undefined}
            >
                <div className="absolute left-4 top-4 z-10 flex items-center gap-2 rounded-full bg-white/92 p-1 shadow-lg backdrop-blur">
                    <button
                        type="button"
                        onClick={() => setColorMode("height")}
                        className={cn(
                            button({
                                intent:
                                    colorMode === "height"
                                        ? "primary"
                                        : "ghost",
                                shape: "pill",
                            })
                        )}
                    >
                        Height
                    </button>

                    <button
                        type="button"
                        onClick={() => setColorMode("image")}
                        disabled={!surfaceData.imageColors}
                        className={cn(
                            button({
                                intent:
                                    colorMode === "image" ? "primary" : "ghost",
                                shape: "pill",
                            })
                        )}
                    >
                        Image
                    </button>

                    <div className="mx-1 h-5 w-px bg-gray-200" />

                    <button
                        type="button"
                        onClick={() => void loadData(true)}
                        disabled={refreshing}
                        className={cn(
                            button({ intent: "ghost", shape: "pill" }),
                            "gap-2"
                        )}
                    >
                        {refreshing ? <Spinner /> : null}
                        <span>{refreshing ? "Refreshing" : "Refresh"}</span>
                    </button>
                </div>

                {error ? (
                    <div
                        className={cn(
                            badge({ intent: "error-pill" }),
                            "absolute bottom-4 left-4 z-10"
                        )}
                    >
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
                        onPickColor={handlePickColor}
                        isPickingActive={isPickingColor}
                        onHover={handleHover}
                        onHoverEnd={handleHoverEnd}
                    />
                    <CameraRig
                        data={surfaceData.grid}
                        stats={surfaceData.stats}
                    />
                </Canvas>

                {isPickingColor && hoverInfo && (
                    <div
                        style={{
                            position: "fixed",
                            left: hoverInfo.x + 16,
                            top: hoverInfo.y - 12,
                            width: 24,
                            height: 24,
                            borderRadius: "50%",
                            backgroundColor: hoverInfo.color,
                            border: "2px solid white",
                            boxShadow:
                                "0 0 0 1px rgba(0,0,0,0.25), 0 2px 4px rgba(0,0,0,0.15)",
                            pointerEvents: "none",
                            zIndex: 50,
                        }}
                    />
                )}
            </div>
        );
    }
    return <div className="w-full">{mainCanvas}</div>;
}
