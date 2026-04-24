import { createContext, useContext } from "react";
import type { ProjectConfigOutput } from "@/client";
import type { Action as ProjectAction } from "./projectReducer";

const ProjectStateContext = createContext<ProjectConfigOutput | null>(null);
const ProjectDispatchContext =
    createContext<React.Dispatch<ProjectAction> | null>(null);

export { ProjectStateContext, ProjectDispatchContext };

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
