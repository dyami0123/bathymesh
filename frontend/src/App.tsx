import "./index.css";

import { ContourOptions } from "./components/ConfigForms/ContourOptions";
import { ProjectConfigYaml } from "./components/ProjectConfigYaml";
import type { ProjectConfigOutput } from "./client";

import { defaultsApiConfigDefaultsGet } from "./client";
import { useEffect, useState } from "react";
import { ProjectProvider } from "./state/projectContext";
import { PostProcessingConfig } from "./components/ConfigForms/PostProcessingConfig";
import { ConfigEditor } from "./components/ConfigEditor";
import { Runner } from "./components/Runner";
import { ImageUpload } from "./components/ImageUpload";
import { HeightmapViewer } from "./components/HeightmapViewer";
import type { ImageData, HeightmapDataJson } from "./client";

export function App() {
    const [initialProject, setInitialProject] =
        useState<ProjectConfigOutput | null>(null);

    const [activeImageData, setActiveImageData] = useState<ImageData | null>(
        null
    );

    const [activeHeightmapData, setActiveHeightmapData] =
        useState<HeightmapDataJson | null>(null);
    const [viewerRefreshSignal, setViewerRefreshSignal] = useState(0);
    const [isHeightmapViewerLoading, setIsHeightmapViewerLoading] =
        useState(true);

    useEffect(() => {
        defaultsApiConfigDefaultsGet().then((result) => {
            setInitialProject(result.data ?? null);
        });
    }, []);

    if (!initialProject) return <div>Loading...</div>;

    return (
        <ProjectProvider initialProject={initialProject}>
            <div className="min-h-screen w-full p-4 lg:p-6">
                <div className="flex w-full flex-col gap-4">
                    <HeightmapViewer
                        activeImageData={activeImageData}
                        setActiveImageData={setActiveImageData}
                        activeHeightmapData={activeHeightmapData}
                        setActiveHeightmapData={setActiveHeightmapData}
                        refreshSignal={viewerRefreshSignal}
                        loading={isHeightmapViewerLoading}
                        setLoading={setIsHeightmapViewerLoading}
                    />
                    <ImageUpload
                        setActiveImageData={setActiveImageData}
                        setActiveHeightmapData={setActiveHeightmapData}
                        setHeightmapViewerLoading={setIsHeightmapViewerLoading}
                        onUploaded={() =>
                            setViewerRefreshSignal((value) => value + 1)
                        }
                    />
                </div>
            </div>
        </ProjectProvider>
    );
}

export default App;
