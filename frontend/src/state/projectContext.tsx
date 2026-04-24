import { createContext, useContext } from "react";
import type { ProjectConfigOutput } from "@/client";
import type { Action as ProjectAction } from "./projectReducer";

const ProjectStateContext = createContext<ProjectConfigOutput | null>(null);
const ProjectDispatchContext =
    createContext<React.Dispatch<ProjectAction> | null>(null);

type ProjectSelectionState = {
    projectOptions: string[];
    selectedProjectId: string;
    setSelectedProjectId: (projectId: string) => void;
    isProjectLoading: boolean;
};

const ProjectSelectionContext = createContext<ProjectSelectionState | null>(
    null
);

export { ProjectStateContext, ProjectDispatchContext, ProjectSelectionContext };

export function useProjectOptional(): ProjectConfigOutput | null {
    return useContext(ProjectStateContext);
}

export function useProject(): ProjectConfigOutput {
    const ctx = useContext(ProjectStateContext);
    if (!ctx)
        throw new Error("useProject must be used inside ProjectStateProvider");
    return ctx;
}

export function useProjectDispatch(): React.Dispatch<ProjectAction> {
    const ctx = useContext(ProjectDispatchContext);
    if (!ctx)
        throw new Error(
            "useProjectDispatch must be used inside ProjectStateProvider"
        );
    return ctx;
}

export function useProjectSelectionState(): ProjectSelectionState {
    const ctx = useContext(ProjectSelectionContext);
    if (!ctx)
        throw new Error(
            "useProjectSelectionState must be used inside ProjectStateProvider"
        );
    return ctx;
}
