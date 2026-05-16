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
import { TabbedContent } from "./components/ui/TabedContent";
import { ProjectConfigYaml } from "./components/ProjectConfigYaml";
import { ColorMapConfigEditor } from "./components/ColorMapConfigEditor";
import { cn } from "@/lib/cn";

export function App() {
    return (
        <div className="background-white min-h-screen `">
            <ProjectStateProvider>
                <ProjectAppShell />
            </ProjectStateProvider>
        </div>
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
                    <div className="flex w-full flex-col gap-4 bg-white h-full">
                        <div className="flex w-full">
                            <HeightmapViewer />
                            <div className="w-1/2">
                                {TabbedContent([
                                    {
                                        id: "Colormap Editor",
                                        label: "Colormap Editor",
                                        content: <ColorMapConfigEditor />,
                                    },
                                    {
                                        id: "Image Upload",
                                        label: "Image Upload",
                                        content: <ImageUpload />,
                                    },
                                    {
                                        id: "Project Config YAML",
                                        label: "Project Config YAML",
                                        content: <ProjectConfigYaml />,
                                    },
                                ])}
                            </div>
                        </div>
                        <div className="flex w-full justify-center ">
                            <Card className="w-8/10">
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
                                    className={cn(select())}
                                >
                                    {projectOptions.map((projectId) => (
                                        <option
                                            key={projectId}
                                            value={projectId}
                                        >
                                            {projectId}
                                        </option>
                                    ))}
                                </select>
                            </Card>
                        </div>
                    </div>
                </div>
            </ColormapStateProvider>
        </ViewerStateProvider>
    );
}

export default App;
