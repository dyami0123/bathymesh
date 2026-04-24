import { useCallback, useEffect, useMemo, useReducer, useRef } from "react";
import type { ProjectConfigOutput } from "@/client";
import { projectReducer, type Action as ProjectAction } from "./projectReducer";
import {
    getProjectConfigApiConfigProjectIdGet,
    setProjectConfigApiConfigProjectIdPut,
    type ProjectConfigInput,
} from "@/client";
import {
    ProjectStateContext,
    ProjectDispatchContext,
    ProjectSelectionContext,
} from "./projectContext";
import {
    addProjectId,
    fetchProjectIdsFromApi,
    getStoredProjectIds,
    getStoredSelectedProjectId,
    saveStoredProjectIds,
    saveStoredSelectedProjectId,
} from "@/projectStorage";
import {
    projectSessionReducer,
    SESSION_INITIAL_STATE,
} from "./projectSessionReducer";

export function ProjectStateProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    const [sessionState, sessionDispatch] = useReducer(
        projectSessionReducer,
        SESSION_INITIAL_STATE
    );
    const hasMountedRef = useRef(false);
    const projectDebounceRef = useRef<number | null>(null);
    const loadRequestIdRef = useRef(0);
    const skipNextSyncRef = useRef(false);

    useEffect(() => {
        const initializeProjectSelection = async () => {
            sessionDispatch({
                type: "set_project_loading",
                isProjectLoading: true,
            });

            const storedProjectIds = getStoredProjectIds();
            let apiProjectIds: string[] = [];
            try {
                apiProjectIds = await fetchProjectIdsFromApi();
            } catch (error) {
                console.warn("Failed to fetch project list from API", error);
            }

            const seededOptions = [
                ...apiProjectIds,
                ...storedProjectIds,
            ].filter((value, index, values) => values.indexOf(value) === index);

            saveStoredProjectIds(seededOptions);

            const storedSelectedProjectId = getStoredSelectedProjectId();
            const initialSelectedProjectId =
                storedSelectedProjectId &&
                seededOptions.includes(storedSelectedProjectId)
                    ? storedSelectedProjectId
                    : (seededOptions[0] ?? "");

            sessionDispatch({
                type: "initialize",
                projectOptions: seededOptions,
                selectedProjectId: initialSelectedProjectId,
            });

            if (!initialSelectedProjectId) {
                sessionDispatch({
                    type: "set_project_loading",
                    isProjectLoading: false,
                });
            }
        };

        void initializeProjectSelection();
    }, []);

    useEffect(() => {
        const selectedProjectId = sessionState.selectedProjectId;
        if (!selectedProjectId) {
            return;
        }

        if (selectedProjectId === sessionState.project?.project_id) {
            return;
        }

        const requestId = loadRequestIdRef.current + 1;
        loadRequestIdRef.current = requestId;

        const loadSelectedProject = async () => {
            sessionDispatch({
                type: "set_project_loading",
                isProjectLoading: true,
            });

            try {
                const result = await getProjectConfigApiConfigProjectIdGet({
                    path: { project_id: selectedProjectId },
                    throwOnError: true,
                });

                if (!result.data || requestId !== loadRequestIdRef.current) {
                    return;
                }

                skipNextSyncRef.current = true;
                sessionDispatch({ type: "set_project", project: result.data });
                saveStoredSelectedProjectId(selectedProjectId);
                saveStoredProjectIds(
                    addProjectId(sessionState.projectOptions, selectedProjectId)
                );
            } catch (error) {
                console.error("Failed to load project", error);
            } finally {
                if (requestId === loadRequestIdRef.current) {
                    sessionDispatch({
                        type: "set_project_loading",
                        isProjectLoading: false,
                    });
                }
            }
        };

        void loadSelectedProject();
    }, [
        sessionState.selectedProjectId,
        sessionState.project?.project_id,
        sessionState.projectOptions,
    ]);

    const setSelectedProjectId = useCallback((selectedProjectId: string) => {
        sessionDispatch({ type: "set_selected_project_id", selectedProjectId });
    }, []);

    const projectDispatch = useCallback((action: ProjectAction) => {
        sessionDispatch({ type: "apply_project_action", action });
    }, []);

    const selectionState = useMemo(
        () => ({
            projectOptions: sessionState.projectOptions,
            selectedProjectId: sessionState.selectedProjectId,
            setSelectedProjectId,
            isProjectLoading: sessionState.isProjectLoading,
        }),
        [
            sessionState.projectOptions,
            sessionState.selectedProjectId,
            sessionState.isProjectLoading,
            setSelectedProjectId,
        ]
    );

    useEffect(() => {
        if (!sessionState.project) {
            return;
        }
        const currentProject = sessionState.project;

        if (!hasMountedRef.current) {
            hasMountedRef.current = true;
            return;
        }

        if (skipNextSyncRef.current) {
            skipNextSyncRef.current = false;
            return;
        }

        if (projectDebounceRef.current !== null) {
            window.clearTimeout(projectDebounceRef.current);
        }

        projectDebounceRef.current = window.setTimeout(() => {
            const syncProjectConfig = async () => {
                try {
                    await setProjectConfigApiConfigProjectIdPut({
                        path: { project_id: currentProject.project_id },
                        body: currentProject as ProjectConfigInput,
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
    }, [sessionState.project]);

    return (
        <ProjectSelectionContext.Provider value={selectionState}>
            <ProjectStateContext.Provider value={sessionState.project}>
                <ProjectDispatchContext.Provider value={projectDispatch}>
                    {children}
                </ProjectDispatchContext.Provider>
            </ProjectStateContext.Provider>
        </ProjectSelectionContext.Provider>
    );
}
