import "./index.css";

import { ConfigEditor } from "./components/ConfigEditor";
import { ImageUpload } from "./components/ImageUpload";
import { HeightmapViewer } from "./components/HeightmapViewer";
import { ProjectStateProvider } from "./state/ProjectStateProvider";
import { ViewerStateProvider } from "./state/ViewerStateProvider";
import { ColormapStateProvider } from "./state/ColormapStateProvider";
import {
    useProjectOptional,
    useProjectSelectionState,
} from "./state/projectContext";

export function App() {
    return (
        <ProjectStateProvider>
            <ProjectAppShell />
        </ProjectStateProvider>
    );
}

function ProjectAppShell() {
    const {
        projectOptions,
        selectedProjectId,
        setSelectedProjectId,
        isProjectLoading,
    } = useProjectSelectionState();
    const project = useProjectOptional();

    if (isProjectLoading) {
        return <div>Loading project...</div>;
    }

    if (!project) {
        return (
            <div>No projects found. Upload an image to create a project.</div>
        );
    }

    return (
        <ViewerStateProvider>
            <ColormapStateProvider>
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
                        <HeightmapViewer />
                        <ImageUpload />
                        <ConfigEditor />
                    </div>
                </div>
            </ColormapStateProvider>
        </ViewerStateProvider>
    );
}

export default App;
