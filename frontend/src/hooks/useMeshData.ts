import { useState, useCallback } from "react";
import { useProject } from "@/state/projectContext";
import {
    getProjectMeshApiMeshdataProjectIdGet,
    calculateProjectMeshApiMeshdataProjectIdPost,
    getJobStatusApiJobsJobIdGet,
    calculateProjectHeightmapApiHeightmapProjectIdPost,
} from "@/client";
import type { JobStatus, MeshDataJson } from "@/client";

const POLL_INTERVAL_MS = 1000;

type MeshState =
    | { type: "idle" }
    | { type: "calculating"; jobId: string }
    | { type: "loaded"; data: MeshDataJson }
    | { type: "error"; message: string };

export function useMeshData() {
    const project = useProject();
    const [meshState, setMeshState] = useState<MeshState>({ type: "idle" });
    const [isLoading, setIsLoading] = useState(false);

    const calculateMesh = useCallback(async () => {
        setMeshState({ type: "idle" });
        setIsLoading(true);
        console.log(
            "[useMeshData] Starting heightmap calculation (non-preview) for project:",
            project.project_id
        );

        try {
            // // Step 1: Submit heightmap calculation (non-preview)
            const heightmapResponse =
                await calculateProjectHeightmapApiHeightmapProjectIdPost({
                    path: { project_id: project.project_id },
                    body: { is_preview: false },
                    throwOnError: true,
                });

            const heightmapJobId = heightmapResponse.data.jobId;
            console.log(
                "[useMeshData] Heightmap calculation job submitted with ID:",
                heightmapJobId
            );

            // Step 2: Poll heightmap job until complete
            const pollHeightmapStatus = async (): Promise<void> => {
                return new Promise((resolve, reject) => {
                    const poll = async () => {
                        try {
                            const statusResponse =
                                await getJobStatusApiJobsJobIdGet({
                                    path: { job_id: heightmapJobId },
                                    throwOnError: true,
                                });

                            const status = statusResponse.data;
                            console.log(
                                "[useMeshData] Heightmap job status:",
                                status.status,
                                "- Job ID:",
                                heightmapJobId
                            );

                            if (status.status === "completed") {
                                console.log(
                                    "[useMeshData] Heightmap job completed"
                                );
                                resolve();
                            } else if (status.status === "failed") {
                                console.error(
                                    "[useMeshData] Heightmap job failed:",
                                    status.error
                                );
                                reject(
                                    new Error(
                                        status.error ||
                                            "Heightmap calculation failed"
                                    )
                                );
                            } else {
                                setTimeout(poll, POLL_INTERVAL_MS);
                            }
                        } catch (error) {
                            console.error(
                                "[useMeshData] Error checking heightmap job status:",
                                error
                            );
                            reject(error);
                        }
                    };
                    poll();
                });
            };

            await pollHeightmapStatus();

            // Step 3: Submit mesh calculation job
            console.log(
                "[useMeshData] Starting mesh calculation for project:",
                project.project_id
            );
            const meshResponse =
                await calculateProjectMeshApiMeshdataProjectIdPost({
                    path: { project_id: project.project_id },
                    throwOnError: true,
                    body: {},
                });

            const meshJobId = meshResponse.data.jobId;
            console.log(
                "[useMeshData] Mesh calculation job submitted with ID:",
                meshJobId
            );
            setMeshState({ type: "calculating", jobId: meshJobId });

            // Step 4: Poll mesh job until complete
            const pollMeshStatus = async () => {
                try {
                    const statusResponse = await getJobStatusApiJobsJobIdGet({
                        path: { job_id: meshJobId },
                        throwOnError: true,
                    });

                    const status = statusResponse.data;
                    console.log(
                        "[useMeshData] Mesh job status:",
                        status.status,
                        "- Job ID:",
                        meshJobId
                    );

                    if (status.status === "completed") {
                        console.log(
                            "[useMeshData] Mesh job completed, fetching mesh data"
                        );
                        // Fetch the mesh data
                        try {
                            const meshDataResponse =
                                await getProjectMeshApiMeshdataProjectIdGet({
                                    path: { project_id: project.project_id },
                                    query: { is_preview: false },
                                    throwOnError: true,
                                });
                            console.log("[useMeshData] Mesh data received:", {
                                vertexCount:
                                    meshDataResponse.data.vertices.length,
                                triangleCount:
                                    meshDataResponse.data.triangles.length,
                            });
                            setMeshState({
                                type: "loaded",
                                data: meshDataResponse.data,
                            });
                        } catch (error) {
                            console.error(
                                "[useMeshData] Failed to fetch mesh data:",
                                error
                            );
                            setMeshState({
                                type: "error",
                                message: `Failed to fetch mesh data: ${error instanceof Error ? error.message : String(error)}`,
                            });
                        }
                    } else if (status.status === "failed") {
                        console.error(
                            "[useMeshData] Mesh job failed:",
                            status.error
                        );
                        setMeshState({
                            type: "error",
                            message: status.error || "Mesh calculation failed",
                        });
                    } else {
                        // Still processing, continue polling
                        setTimeout(pollMeshStatus, POLL_INTERVAL_MS);
                    }
                } catch (error) {
                    console.error(
                        "[useMeshData] Error checking mesh job status:",
                        error
                    );
                    setMeshState({
                        type: "error",
                        message: `Failed to check mesh job status: ${error instanceof Error ? error.message : String(error)}`,
                    });
                }
            };

            // Start polling mesh job
            pollMeshStatus();
        } catch (error) {
            console.error(
                "[useMeshData] Failed to submit heightmap calculation:",
                error
            );
            setMeshState({
                type: "error",
                message: `Failed to submit heightmap calculation: ${error instanceof Error ? error.message : String(error)}`,
            });
            setIsLoading(false);
        }
    }, [project.project_id]);

    const viewMesh = useCallback(async () => {
        console.log(
            "[useMeshData] Fetching existing mesh for project:",
            project.project_id
        );
        setIsLoading(true);
        try {
            const response = await getProjectMeshApiMeshdataProjectIdGet({
                path: { project_id: project.project_id },
                query: { is_preview: false },
                throwOnError: true,
            });
            console.log("[useMeshData] Mesh data fetched successfully:", {
                vertexCount: response.data.vertices.length,
                triangleCount: response.data.triangles.length,
            });
            setMeshState({ type: "loaded", data: response.data });
        } catch (error) {
            console.error("[useMeshData] Failed to fetch mesh:", error);
            setMeshState({
                type: "error",
                message: `Failed to fetch mesh: ${error instanceof Error ? error.message : String(error)}`,
            });
        } finally {
            setIsLoading(false);
        }
    }, [project.project_id]);

    const clearMesh = useCallback(() => {
        console.log("[useMeshData] Clearing mesh");
        setMeshState({ type: "idle" });
    }, []);

    return {
        meshState,
        isLoading,
        calculateMesh,
        viewMesh,
        clearMesh,
    };
}
