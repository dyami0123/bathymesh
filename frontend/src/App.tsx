import "./index.css";

import { calculateProjectHeightmapApiHeightmapProjectIdPost } from "./client";
import { useCallback, useEffect, useRef, useState } from "react";
import { ProjectProvider } from "./state/projectContext";
import { ConfigEditor } from "./components/ConfigEditor";
import { ImageUpload } from "./components/ImageUpload";
import { HeightmapViewer, PREVIEW_DIM } from "./components/HeightmapViewer";
import type { ImageData, HeightmapDataJson } from "./client";
import { blockingApiCall } from "./blockingApiCall";
import { useProjectSelection } from "./hooks/useProjectSelection";

export function App() {
    const {
        initialProject,
        projectOptions,
        selectedProjectId,
        setSelectedProjectId,
        isProjectLoading,
    } = useProjectSelection();

    const [activeImageData, setActiveImageData] = useState<ImageData | null>(
        null
    );

    const [activeHeightmapData, setActiveHeightmapData] =
        useState<HeightmapDataJson | null>(null);
    const [viewerRefreshSignal, setViewerRefreshSignal] = useState(0);
    const [isHeightmapViewerLoading, setIsHeightmapViewerLoading] =
        useState(true);
    const colorMapRecomputeDebounceRef = useRef<number | null>(null);
    const [pickedColor, setPickedColor] = useState<string | null>(null);
    const [isPickingColor, setIsPickingColor] = useState(false);

    const recomputePreviewFromColorMap = useCallback(
        async (projectId: string) => {
            setIsHeightmapViewerLoading(true);
            try {
                await blockingApiCall({
                    endpoint:
                        calculateProjectHeightmapApiHeightmapProjectIdPost,
                    project_id: projectId,
                    body: {
                        is_preview: true,
                        max_dimension_override: PREVIEW_DIM,
                    },
                });

                setViewerRefreshSignal((value) => value + 1);
            } catch (error) {
                console.error(
                    "Failed to recompute preview heightmap from colormap changes",
                    error
                );
                setIsHeightmapViewerLoading(false);
            }
        },
        []
    );

    const handleColorMapChanged = useCallback(() => {
        if (!selectedProjectId) {
            return;
        }

        if (colorMapRecomputeDebounceRef.current !== null) {
            window.clearTimeout(colorMapRecomputeDebounceRef.current);
        }

        colorMapRecomputeDebounceRef.current = window.setTimeout(() => {
            void recomputePreviewFromColorMap(selectedProjectId);
        }, 1000);
    }, [recomputePreviewFromColorMap, selectedProjectId]);

    useEffect(() => {
        return () => {
            if (colorMapRecomputeDebounceRef.current !== null) {
                window.clearTimeout(colorMapRecomputeDebounceRef.current);
            }
        };
    }, []);

    useEffect(() => {
        setActiveImageData(null);
        setActiveHeightmapData(null);
        setViewerRefreshSignal(0);
        setIsHeightmapViewerLoading(true);
    }, [initialProject?.project_id]);

    if (isProjectLoading) {
        return <div>Loading project...</div>;
    }

    if (!initialProject) {
        return (
            <div>No projects found. Upload an image to create a project.</div>
        );
    }

    return (
        <ProjectProvider
            key={initialProject.project_id}
            initialProject={initialProject}
        >
            <div className="min-h-screen w-full p-4 lg:p-6">
                <div className="flex w-full flex-col gap-4">
                    <div className="rounded-lg border border-gray-300 bg-white p-4 shadow-sm">
                        <label
                            htmlFor="selected-project"
                            className="mb-2 block text-sm font-medium text-gray-700"
                        >
                            Selected Project
                        </label>
                        <select
                            id="selected-project"
                            value={selectedProjectId}
                            onChange={(event) =>
                                setSelectedProjectId(event.target.value)
                            }
                            className="w-full rounded border border-gray-300 px-3 py-2 text-sm text-gray-900"
                        >
                            {projectOptions.map((projectId) => (
                                <option key={projectId} value={projectId}>
                                    {projectId}
                                </option>
                            ))}
                        </select>
                    </div>
                    <HeightmapViewer
                        activeImageData={activeImageData}
                        setActiveImageData={setActiveImageData}
                        activeHeightmapData={activeHeightmapData}
                        setActiveHeightmapData={setActiveHeightmapData}
                        refreshSignal={viewerRefreshSignal}
                        loading={isHeightmapViewerLoading}
                        setLoading={setIsHeightmapViewerLoading}
                        onPickColor={(hex) => {
                            console.debug("[color-pick] App received", hex);
                            setPickedColor(hex);
                        }}
                        isPickingColor={isPickingColor}
                    />
                    <ImageUpload
                        setActiveImageData={setActiveImageData}
                        setActiveHeightmapData={setActiveHeightmapData}
                        setHeightmapViewerLoading={setIsHeightmapViewerLoading}
                        onUploaded={() =>
                            setViewerRefreshSignal((value) => value + 1)
                        }
                    />
                    <ConfigEditor
                        onColorMapChanged={handleColorMapChanged}
                        pickedColor={pickedColor}
                        onPickedColorConsumed={() => setPickedColor(null)}
                        onPickModeChanged={setIsPickingColor}
                    />
                </div>
            </div>
        </ProjectProvider>
    );
}

export default App;
