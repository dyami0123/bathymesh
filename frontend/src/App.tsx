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
import { Card } from "./components/ui/Card";
import { label, select } from "./components/ui/styles";

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
                        <Card>
                            <label
                                htmlFor="selected-project"
                                className={label()}
                            >
                                Selected Project
                            </label>
                            <select
                                id="selected-project"
                                value={selectedProjectId}
                                onChange={(event) =>
                                    setSelectedProjectId(event.target.value)
                                }
                                className={select()}
                            >
                                {projectOptions.map((projectId) => (
                                    <option key={projectId} value={projectId}>
                                        {projectId}
                                    </option>
                                ))}
                            </select>
                        </Card>
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
