import { useCallback, useEffect, useRef, useState } from "react";
import {
    getProjectHeightmapApiHeightmapProjectIdGet,
    getProjectImageApiImageProjectIdGet,
    calculateProjectHeightmapApiHeightmapProjectIdPost,
} from "@/client";
import type { HeightmapDataJson } from "@/client";
import type { SurfaceData } from "@/data_processing";
import { buildHeightColorArray } from "@/data_processing/heightColormap";
import { getImageColorsFromBlob } from "@/data_processing/imageProcessing";
import { blockingApiCall } from "@/blockingApiCall";
import { useProject } from "@/state/projectContext";
import { useViewer, useViewerDispatch } from "@/state/viewerContext";
import { PREVIEW_DIM } from "@/constants/viewer";
import type { ImageData } from "@/types/imageData";

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

export type TerrainSurfaceState = {
    surfaceData: SurfaceData | null;
    loading: boolean;
    refreshing: boolean;
    error: string | null;
    isFirstLoad: boolean;
    refreshSurfaceData: () => Promise<void>;
};

export function useTerrainSurfaceData(): TerrainSurfaceState {
    const project = useProject();
    const {
        activeImageData,
        activeHeightmapData,
        refreshSignal,
        isLoading: loading,
    } = useViewer();
    const viewerDispatch = useViewerDispatch();

    const [surfaceData, setSurfaceData] = useState<SurfaceData | null>(null);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isFirstLoad, setIsFirstLoad] = useState(true);

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

    const loadData = useCallback(
        async (forceRefresh = false) => {
            const firstLoadPending = !hasInitialDataRef.current;

            let resolvedImageData = normalizeImagePayload(
                activeImageDataRef.current
            );
            let resolvedHeightmapData = activeHeightmapDataRef.current;

            if (forceRefresh) {
                resolvedImageData = null;
                resolvedHeightmapData = null;
            }

            if (firstLoadPending) {
                setLoading(true);
                const existingHeightmapResult =
                    await getProjectHeightmapApiHeightmapProjectIdGet({
                        path: { project_id: project.project_id },
                        throwOnError: true,
                        query: { is_preview: true },
                    });

                if (!existingHeightmapResult.data?.data) {
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

                const filled = raw.map((row) =>
                    row.map((v) => (v == null || Number.isNaN(v) ? 0 : v))
                );

                const minVal = filled.reduce(
                    (min, row) =>
                        Math.min(
                            min,
                            ...row.map((v) =>
                                v == null || Number.isNaN(v) ? Infinity : v
                            )
                        ),
                    Infinity
                );

                const maxVal = filled.reduce(
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
                    min: minVal,
                    max: maxVal,
                };
                const heightColors = buildHeightColorArray(filled, stats);

                let imageColors: Float32Array | null = null;
                if (resolvedImageData) {
                    imageColors = await getImageColorsFromBlob(
                        filled,
                        resolvedImageData
                    );
                }

                setSurfaceData({
                    grid: filled,
                    stats,
                    heightColors,
                    imageColors,
                });
            } catch (err) {
                const message =
                    err instanceof Error
                        ? err.message
                        : "Failed to fetch surface data";
                setError(message);
            } finally {
                hasInitialDataRef.current = true;
                setIsFirstLoad(false);
                setLoading(false);
                setRefreshing(false);
            }
        },
        [
            project.project_id,
            setActiveHeightmapData,
            setActiveImageData,
            setLoading,
        ]
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

    const refreshSurfaceData = useCallback(async () => {
        await loadData(true);
    }, [loadData]);

    return {
        surfaceData,
        loading,
        refreshing,
        error,
        isFirstLoad,
        refreshSurfaceData,
    };
}
