import { useEffect, useReducer, useRef } from "react";
import type { ProjectConfigOutput } from "@/client";
import { projectReducer } from "./projectReducer";
import {
    setProjectConfigApiConfigProjectIdPut,
    type ProjectConfigInput,
} from "@/client";
import { ProjectStateContext, ProjectDispatchContext } from "./projectContext";

export function ProjectStateProvider({
    initialProject,
    children,
}: {
    initialProject: ProjectConfigOutput;
    children: React.ReactNode;
}) {
    // Project state (migrated from ProjectProvider)
    const [projectState, projectDispatch] = useReducer(
        projectReducer,
        initialProject
    );
    const hasMountedRef = useRef(false);
    const projectDebounceRef = useRef<number | null>(null);

    useEffect(() => {
        if (!hasMountedRef.current) {
            hasMountedRef.current = true;
            return;
        }

        if (projectDebounceRef.current !== null) {
            window.clearTimeout(projectDebounceRef.current);
        }

        projectDebounceRef.current = window.setTimeout(() => {
            const syncProjectConfig = async () => {
                try {
                    await setProjectConfigApiConfigProjectIdPut({
                        path: { project_id: projectState.project_id },
                        body: projectState as ProjectConfigInput,
                        throwOnError: true,
                    });
                } catch (error) {
                    console.error("Failed to sync project config", error);
                }
            };

            void syncProjectConfig();
        }, 350);

        return () => {
            if (projectDebounceRef.current !== null) {
                window.clearTimeout(projectDebounceRef.current);
            }
        };
    }, [projectState]);

    return (
        <ProjectStateContext.Provider value={projectState}>
            <ProjectDispatchContext.Provider value={projectDispatch}>
                {children}
            </ProjectDispatchContext.Provider>
        </ProjectStateContext.Provider>
    );
}
