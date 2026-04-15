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
import { HeightmapViewer } from "./components/HeightmapViewer";

export function App() {
    const [initialProject, setInitialProject] =
        useState<ProjectConfigOutput | null>(null);

    useEffect(() => {
        defaultsApiConfigDefaultsGet().then((result) => {
            setInitialProject(result.data ?? null);
        });
    }, []);

    if (!initialProject) return <div>Loading...</div>;

    <div className="lg:col-span-2">
        {/* <ConfigEditor /> */}
        {/* <Runner /> */}
    </div>;
    return (
        <ProjectProvider initialProject={initialProject}>
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
                {/* Configuration and controls on the left */}
                {/* Heightmap visualization on the right */}
                <div>
                    <HeightmapViewer />
                </div>
            </div>
        </ProjectProvider>
    );
}

export default App;
