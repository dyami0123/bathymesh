import { listProjectsApiProjectsGet } from "./client";

const RECENT_PROJECTS_KEY = "bathymesh.recentProjectIds";
const SELECTED_PROJECT_KEY = "bathymesh.selectedProjectId";

export function getStoredProjectIds(): string[] {
    if (typeof window === "undefined") {
        return [];
    }

    try {
        const raw = window.localStorage.getItem(RECENT_PROJECTS_KEY);
        if (!raw) {
            return [];
        }

        const parsed = JSON.parse(raw);
        if (!Array.isArray(parsed)) {
            return [];
        }

        return parsed.filter(
            (item): item is string =>
                typeof item === "string" && item.trim().length > 0
        );
    } catch {
        return [];
    }
}

export function saveStoredProjectIds(projectIds: string[]): void {
    if (typeof window === "undefined") {
        return;
    }

    window.localStorage.setItem(
        RECENT_PROJECTS_KEY,
        JSON.stringify(projectIds)
    );
}

export function getStoredSelectedProjectId(): string {
    if (typeof window === "undefined") {
        return "";
    }

    return window.localStorage.getItem(SELECTED_PROJECT_KEY) ?? "";
}

export function saveStoredSelectedProjectId(projectId: string): void {
    if (typeof window === "undefined") {
        return;
    }

    window.localStorage.setItem(SELECTED_PROJECT_KEY, projectId);
}

export async function fetchProjectIdsFromApi(): Promise<string[]> {
    const result = await listProjectsApiProjectsGet({
        throwOnError: true,
    });
    const data = result.data;

    if (!Array.isArray(data)) {
        return [];
    }

    return data.filter(
        (item): item is string =>
            typeof item === "string" && item.trim().length > 0
    );
}

export function addProjectId(
    projectIds: string[],
    projectId: string
): string[] {
    const deduped = [projectId, ...projectIds.filter((id) => id !== projectId)];
    return deduped.slice(0, 15);
}
