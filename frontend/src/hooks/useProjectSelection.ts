import { useEffect, useState } from "react";

import type { ProjectConfigOutput } from "../client";
import { getProjectConfigApiConfigProjectIdGet } from "../client";
import {
    addProjectId,
    fetchProjectIdsFromApi,
    getStoredProjectIds,
    getStoredSelectedProjectId,
    saveStoredProjectIds,
    saveStoredSelectedProjectId,
} from "../projectStorage";

interface UseProjectSelectionResult {
    initialProject: ProjectConfigOutput | null;
    projectOptions: string[];
    selectedProjectId: string;
    setSelectedProjectId: (id: string) => void;
    isProjectLoading: boolean;
}

export function useProjectSelection(): UseProjectSelectionResult {
    const [initialProject, setInitialProject] =
        useState<ProjectConfigOutput | null>(null);
    const [projectOptions, setProjectOptions] = useState<string[]>([]);
    const [selectedProjectId, setSelectedProjectId] = useState<string>("");
    const [isProjectLoading, setIsProjectLoading] = useState(true);

    useEffect(() => {
        const initializeProjectSelection = async () => {
            setIsProjectLoading(true);
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

            setProjectOptions(seededOptions);
            saveStoredProjectIds(seededOptions);

            const storedSelectedProjectId = getStoredSelectedProjectId();
            const initialSelectedProjectId =
                storedSelectedProjectId &&
                seededOptions.includes(storedSelectedProjectId)
                    ? storedSelectedProjectId
                    : (seededOptions[0] ?? "");

            setSelectedProjectId(initialSelectedProjectId);

            if (!initialSelectedProjectId) {
                setIsProjectLoading(false);
            }
        };

        void initializeProjectSelection();
    }, []);

    useEffect(() => {
        if (!selectedProjectId) {
            return;
        }

        if (selectedProjectId === initialProject?.project_id) {
            return;
        }

        const loadSelectedProject = async () => {
            setIsProjectLoading(true);

            try {
                const result = await getProjectConfigApiConfigProjectIdGet({
                    path: { project_id: selectedProjectId },
                    throwOnError: true,
                });

                if (!result.data) {
                    return;
                }

                setInitialProject(result.data);
                saveStoredSelectedProjectId(selectedProjectId);

                const nextOptions = addProjectId(
                    projectOptions,
                    selectedProjectId
                );
                setProjectOptions(nextOptions);
                saveStoredProjectIds(nextOptions);
            } catch (error) {
                console.error("Failed to load project", error);
            } finally {
                setIsProjectLoading(false);
            }
        };

        void loadSelectedProject();
    }, [selectedProjectId, initialProject?.project_id, projectOptions]);

    return {
        initialProject,
        projectOptions,
        selectedProjectId,
        setSelectedProjectId,
        isProjectLoading,
    };
}
