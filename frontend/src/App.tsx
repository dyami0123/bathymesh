import "./index.css";

import { ImageUpload } from "./components/ImageUpload";
import { HeightmapViewer } from "./components/HeightmapViewer";
import { ProjectStateProvider } from "./state/ProjectStateProvider";
import { ViewerStateProvider } from "./state/ViewerStateProvider";
import { ColormapStateProvider } from "./state/ColormapStateProvider";
import {
    useProjectOptional,
    useProjectSelectionState,
} from "./state/projectContext";
import { ColorMapConfigEditor } from "./components/ColorMapConfigEditor";
import { MenuPopup } from "./components/ui/MenuPopup";
import { ProjectSelector } from "./components/ProjectSelector";

export function App() {
    return (
        <div className="h-dvh bg-white">
            <ProjectStateProvider>
                <ProjectAppShell />
            </ProjectStateProvider>
        </div>
    );
}

function ProjectAppShell() {
    const { isProjectLoading } = useProjectSelectionState();

    const project = useProjectOptional();

    if (isProjectLoading) {
        return <div>Loading project…</div>;
    }

    if (!project) {
        return (
            <div>No projects found. Upload an image to create a project.</div>
        );
    }

    return (
        <ViewerStateProvider>
            <ColormapStateProvider>
                <div className="h-full w-full p-4 lg:p-6">
                    <div className="flex h-full min-h-0 w-full flex-col gap-4 bg-white">
                        <div className="flex w-full shrink-0 justify-end">
                            <MenuPopup
                                menuLabel="Menu"
                                actions={[
                                    {
                                        id: "upload-image",
                                        label: "Upload image…",
                                        popupTitle: "Upload Image",
                                        content: <ImageUpload inPopup />,
                                    },
                                    {
                                        id: "select-project",
                                        label: "Select project…",
                                        popupTitle: "Select Project",
                                        content: <ProjectSelector inPopup />,
                                    },
                                ]}
                            />
                        </div>
                        <div className="relative min-h-0 w-full flex-1 overflow-hidden rounded-lg">
                            <div className="h-full w-full">
                                <HeightmapViewer />
                            </div>

                            <div className="pointer-events-none absolute inset-y-0 right-0 z-10 flex w-[clamp(18rem,32vw,28rem)] max-w-[calc(100%-0.75rem)] p-2 sm:p-3">
                                <div className="pointer-events-auto h-full w-full">
                                    <ColorMapConfigEditor />
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </ColormapStateProvider>
        </ViewerStateProvider>
    );
}

export default App;
