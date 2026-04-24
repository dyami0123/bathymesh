import type { ProjectConfigOutput } from "@/client";
import { projectReducer, type Action as ProjectAction } from "./projectReducer";
import { addProjectId } from "@/projectStorage";

type ProjectSessionState = {
    project: ProjectConfigOutput | null;
    projectOptions: string[];
    selectedProjectId: string;
    isProjectLoading: boolean;
};

type ProjectSessionAction =
    | {
          type: "initialize";
          projectOptions: string[];
          selectedProjectId: string;
      }
    | { type: "set_selected_project_id"; selectedProjectId: string }
    | { type: "set_project_loading"; isProjectLoading: boolean }
    | { type: "set_project"; project: ProjectConfigOutput }
    | { type: "apply_project_action"; action: ProjectAction };

export const SESSION_INITIAL_STATE: ProjectSessionState = {
    project: null,
    projectOptions: [],
    selectedProjectId: "",
    isProjectLoading: true,
};

export function projectSessionReducer(
    state: ProjectSessionState,
    action: ProjectSessionAction
): ProjectSessionState {
    switch (action.type) {
        case "initialize":
            return {
                ...state,
                projectOptions: action.projectOptions,
                selectedProjectId: action.selectedProjectId,
                isProjectLoading: action.selectedProjectId.length > 0,
            };

        case "set_selected_project_id":
            return {
                ...state,
                selectedProjectId: action.selectedProjectId,
            };

        case "set_project_loading":
            return {
                ...state,
                isProjectLoading: action.isProjectLoading,
            };

        case "set_project": {
            const nextOptions = addProjectId(
                state.projectOptions,
                action.project.project_id
            );
            return {
                ...state,
                project: action.project,
                projectOptions: nextOptions,
                selectedProjectId: action.project.project_id,
            };
        }

        case "apply_project_action":
            if (!state.project) {
                return state;
            }

            return {
                ...state,
                project: projectReducer(state.project, action.action),
            };
    }
}
