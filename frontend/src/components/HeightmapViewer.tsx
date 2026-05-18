import { useCallback, useEffect, useMemo, useState } from "react";
import {
    useColorPicker,
    useColorPickerDispatch,
} from "@/state/colorPickerContext";
import type { ColorMode } from "@/data_processing";
import { Spinner } from "./Spinner";
import { JobSubmitButton } from "./jobSubmitter";
import { HeightmapSceneCanvas } from "./HeightmapSceneCanvas";
import { MeshControls } from "./MeshControls";
import { cn } from "@/lib/cn";
import { button, badge } from "@/components/ui/styles";
import { useTerrainSurfaceData } from "@/hooks/useTerrainSurfaceData";
import { useMeshData } from "@/hooks/useMeshData";

export function HeightmapViewer() {
    const { isPickingColor } = useColorPicker();
    const colorPickerDispatch = useColorPickerDispatch();
    const {
        surfaceData,
        loading,
        refreshing,
        error,
        isFirstLoad,
        refreshSurfaceData,
    } = useTerrainSurfaceData();

    const { meshState, isLoading, calculateMesh, viewMesh, clearMesh } =
        useMeshData();

    const [colorMode, setColorMode] = useState<ColorMode>("height");
    const [heightMode, setHeightMode] = useState<"normalized" | "absolute">(
        "normalized"
    );
    const [showDebugLines, setShowDebugLines] = useState(true);
    const [showHeightmapMesh, setShowHeightmapMesh] = useState(true);
    const [meshWireframe, setMeshWireframe] = useState(false);

    useEffect(() => {
        if (colorMode === "image" && !surfaceData?.imageColors) {
            setColorMode("height");
        }
    }, [colorMode, surfaceData]);

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

    if (loading && isFirstLoad) {
        mainCanvas = (
            <div className="flex h-full min-h-88 w-full items-center justify-center bg-white">
                <div className="flex items-center gap-3 text-sm text-gray-600">
                    <Spinner />
                    <span>Loading surface...</span>
                </div>
            </div>
        );
    } else if (!surfaceData || !activeColors) {
        mainCanvas = (
            <div className="flex h-full min-h-88 w-full items-center justify-center bg-white">
                <p className="text-sm text-red-600">
                    {error ?? "No surface data available."}
                </p>
            </div>
        );
    } else {
        mainCanvas = (
            <div
                className="relative h-full min-h-88 w-full overflow-hidden rounded-lg bg-white"
                style={isPickingColor ? { cursor: "crosshair" } : undefined}
            >
                <div className="absolute left-4 top-4 z-10 flex items-center gap-2 rounded-full bg-white/92 p-1 shadow-lg backdrop-blur border border-red">
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

                    <div className="mx-1 h-5 w-px bg-gray-200 " />

                    <button
                        type="button"
                        onClick={() => setHeightMode("normalized")}
                        className={cn(
                            button({
                                intent:
                                    heightMode === "normalized"
                                        ? "primary"
                                        : "ghost",
                                shape: "pill",
                            })
                        )}
                    >
                        Normalized
                    </button>

                    <button
                        type="button"
                        onClick={() => setHeightMode("absolute")}
                        className={cn(
                            button({
                                intent:
                                    heightMode === "absolute"
                                        ? "primary"
                                        : "ghost",
                                shape: "pill",
                            })
                        )}
                    >
                        Absolute
                    </button>

                    <div className="mx-1 h-5 w-px bg-gray-200 " />

                    <button
                        type="button"
                        onClick={() => setShowDebugLines((prev) => !prev)}
                        className={cn(
                            button({
                                intent: showDebugLines ? "primary" : "ghost",
                                shape: "pill",
                            })
                        )}
                    >
                        Debug
                    </button>

                    <button
                        type="button"
                        onClick={() => setShowHeightmapMesh((prev) => !prev)}
                        className={cn(
                            button({
                                intent: showHeightmapMesh ? "primary" : "ghost",
                                shape: "pill",
                            })
                        )}
                    >
                        Heightmap
                    </button>

                    <button
                        type="button"
                        onClick={() => setMeshWireframe((prev) => !prev)}
                        disabled={meshState.type !== "loaded"}
                        className={cn(
                            button({
                                intent: meshWireframe ? "primary" : "ghost",
                                shape: "pill",
                            })
                        )}
                    >
                        Wireframe
                    </button>

                    <div className="mx-1 h-5 w-px bg-gray-200 " />

                    <button
                        type="button"
                        onClick={() => void refreshSurfaceData()}
                        disabled={refreshing}
                        className={cn(
                            button({ intent: "ghost", shape: "pill" }),
                            "gap-2 "
                        )}
                    >
                        {refreshing ? <Spinner /> : null}
                        <span>{refreshing ? "Refreshing" : "Refresh"}</span>
                    </button>

                    <div className="mx-1 h-5 w-px bg-gray-200 " />

                    <MeshControls
                        isLoading={isLoading}
                        isMeshVisible={meshState.type === "loaded"}
                        hasError={meshState.type === "error"}
                        errorMessage={
                            meshState.type === "error"
                                ? meshState.message
                                : undefined
                        }
                        onCalculate={calculateMesh}
                        onView={viewMesh}
                        onClear={clearMesh}
                    />
                </div>

                {refreshing ? (
                    <div className="absolute bottom-4 left-4 z-10 flex items-center gap-2 rounded-full bg-white/92 p-2 shadow-lg backdrop-blur border border-gray-200">
                        <Spinner />
                    </div>
                ) : null}

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

                <div className="w-full h-full">
                    <HeightmapSceneCanvas
                        surfaceData={surfaceData}
                        activeColors={activeColors}
                        isPickingColor={isPickingColor}
                        isFirstLoad={isFirstLoad}
                        heightMode={heightMode}
                        showDebugLines={showDebugLines}
                        showHeightmapMesh={showHeightmapMesh}
                        meshWireframe={meshWireframe}
                        meshData={
                            meshState.type === "loaded"
                                ? meshState.data
                                : undefined
                        }
                        onPickColor={handlePickColor}
                        onHover={handleHover}
                        onHoverEnd={handleHoverEnd}
                    />
                </div>

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
    return <div className="h-full w-full">{mainCanvas}</div>;
}
