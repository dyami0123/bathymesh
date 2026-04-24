// state/projectContext.tsx

import {
    createContext,
    useContext,
    useEffect,
    useReducer,
    useRef,
} from "react";
import { projectReducer } from "./projectReducer";
import type { Action } from "./projectReducer";
import {
    setProjectConfigApiConfigProjectIdPut,
    type ProjectConfigInput,
    type ProjectConfigOutput,
} from "../client";

const ProjectStateContext = createContext<ProjectConfigOutput | null>(null);
const ProjectDispatchContext = createContext<React.Dispatch<Action> | null>(
    null
);

export function ProjectProvider({
    initialProject,
    children,
}: {
    initialProject: ProjectConfigOutput;
    children: React.ReactNode;
}) {
    const [state, dispatch] = useReducer(projectReducer, initialProject);
    const hasMountedRef = useRef(false);
    const debounceIdRef = useRef<number | null>(null);

    useEffect(() => {
        if (!hasMountedRef.current) {
            hasMountedRef.current = true;
            return;
        }

        if (debounceIdRef.current !== null) {
            window.clearTimeout(debounceIdRef.current);
        }

        debounceIdRef.current = window.setTimeout(() => {
            const syncProjectConfig = async () => {
                try {
                    await setProjectConfigApiConfigProjectIdPut({
                        path: { project_id: state.project_id },
                        body: state as ProjectConfigInput,
                        throwOnError: true,
                    });
                } catch (error) {
                    console.error("Failed to sync project config", error);
                }
            };

            void syncProjectConfig();
        }, 350);

        return () => {
            if (debounceIdRef.current !== null) {
                window.clearTimeout(debounceIdRef.current);
            }
        };
    }, [state]);

    return (
        <ProjectStateContext.Provider value={state}>
            <ProjectDispatchContext.Provider value={dispatch}>
                {children}
            </ProjectDispatchContext.Provider>
        </ProjectStateContext.Provider>
    );
}

export function useProject() {
    const ctx = useContext(ProjectStateContext);
    if (!ctx) throw new Error("useProject must be used inside provider");
    return ctx;
}

export function useProjectDispatch() {
    const ctx = useContext(ProjectDispatchContext);
    if (!ctx)
        throw new Error("useProjectDispatch must be used inside provider");
    return ctx;
}
