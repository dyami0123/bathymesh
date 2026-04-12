// state/projectContext.tsx

import { createContext, useContext, useReducer } from "react";
import { projectReducer } from "./projectReducer";
import type { Action } from "./projectReducer";
import type { ProjectConfigOutput } from "../client";

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
  if (!ctx) throw new Error("useProjectDispatch must be used inside provider");
  return ctx;
}
