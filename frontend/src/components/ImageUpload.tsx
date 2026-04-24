import { useState, useRef } from "react";
import { useProject, useProjectDispatch } from "@/state/projectContext";
import { Spinner } from "./Spinner";
import { blockingApiCall } from "@/blockingApiCall";
import { PREVIEW_DIM } from "./HeightmapViewer";
import {
    calculateProjectHeightmapApiHeightmapProjectIdPost,
    getProjectConfigApiConfigProjectIdGet,
    getProjectHeightmapApiHeightmapProjectIdGet,
    getProjectImageApiImageProjectIdGet,
} from "@/client";
import type { ImageData, HeightmapDataJson } from "@/client";

type UploadState = "idle" | "uploading" | "success" | "error";

function toImageData(payload: unknown): ImageData | null {
    if (payload instanceof Blob || payload instanceof File) {
        const mimeType = payload.type;
        const validType =
            mimeType === "image/png" ||
            mimeType === "image/jpeg" ||
            mimeType === "image/tiff"
                ? mimeType
                : "image/png";

        return {
            data: payload,
            type: validType,
        };
    }

    if (
        payload &&
        typeof payload === "object" &&
        "data" in payload &&
        (payload as { data?: unknown }).data instanceof Blob &&
        "type" in payload
    ) {
        return payload as ImageData;
    }

    return null;
}

export function ImageUpload({
    setActiveImageData,
    setActiveHeightmapData,
    setHeightmapViewerLoading,
    onUploaded,
}: {
    setActiveImageData: (data: ImageData) => void;
    setActiveHeightmapData: (data: HeightmapDataJson) => void;
    setHeightmapViewerLoading: (loading: boolean) => void;
    onUploaded: () => void;
}) {
    const project = useProject();
    const dispatch = useProjectDispatch();
    const [uploadState, setUploadState] = useState<UploadState>("idle");
    const [errorMessage, setErrorMessage] = useState<string>("");
    const [fileName, setFileName] = useState<string>("");
    const fileInputRef = useRef<HTMLInputElement>(null);

    const ALLOWED_TYPES = ["image/png", "image/jpeg", "image/tiff"];

    const handleFileChange = async (
        event: React.ChangeEvent<HTMLInputElement>
    ) => {
        const file = event.target.files?.[0];
        if (!file) return;

        // Validate file type
        if (!ALLOWED_TYPES.includes(file.type)) {
            setErrorMessage(
                `Invalid file type. Allowed types: PNG, JPEG, TIFF`
            );
            setUploadState("error");
            return;
        }

        setFileName(file.name);
        setErrorMessage("");
        await uploadImage(file);
    };

    const uploadImage = async (file: File) => {
        setUploadState("uploading");
        setHeightmapViewerLoading(true);

        try {
            const formData = new FormData();
            formData.append("file", file);

            const response = await fetch(
                `/api/image/${project.project_id}?update_config_colormap=true`,
                {
                    method: "PUT",
                    body: formData,
                }
            );

            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(
                    `Upload failed: ${response.status} ${errorText}`
                );
            }

            setUploadState("success");
            setErrorMessage("");

            await blockingApiCall({
                endpoint: calculateProjectHeightmapApiHeightmapProjectIdPost,
                project_id: project.project_id,
                body: {
                    is_preview: true,
                    max_dimension_override: PREVIEW_DIM,
                },
            });

            const [imageResult, heightmapResult, projectConfigResult] =
                await Promise.all([
                    getProjectImageApiImageProjectIdGet({
                        path: { project_id: project.project_id },
                        throwOnError: true,
                        query: { max_dimension: PREVIEW_DIM },
                    }),
                    getProjectHeightmapApiHeightmapProjectIdGet({
                        path: { project_id: project.project_id },
                        throwOnError: true,
                        query: { is_preview: true },
                    }),
                    getProjectConfigApiConfigProjectIdGet({
                        path: { project_id: project.project_id },
                        throwOnError: true,
                    }),
                ]);

            const normalizedImage = toImageData(imageResult.data);
            if (!normalizedImage) {
                throw new Error(
                    "Failed to load image data after upload. Please refresh and try again."
                );
            }

            if (!heightmapResult.data?.data) {
                throw new Error(
                    "Failed to load heightmap data after upload. Please refresh and try again."
                );
            }

            if (!projectConfigResult.data) {
                throw new Error(
                    "Failed to refresh project config after upload. Please refresh and try again."
                );
            }

            dispatch({
                type: "set_project",
                payload: projectConfigResult.data,
            });

            setActiveImageData(normalizedImage);
            setActiveHeightmapData(heightmapResult.data as HeightmapDataJson);
            onUploaded();

            // Reset the file input
            if (fileInputRef.current) {
                fileInputRef.current.value = "";
            }

            // Clear success message after 3 seconds
            setTimeout(() => {
                setUploadState("idle");
                setFileName("");
            }, 3000);
        } catch (error) {
            setUploadState("error");
            setErrorMessage(
                error instanceof Error
                    ? error.message
                    : "Failed to upload image"
            );
            setHeightmapViewerLoading(false);
        }
    };

    return (
        <div className="w-full rounded-lg border border-gray-300 bg-white p-6 shadow-sm">
            <h2 className="mb-4 text-lg font-semibold text-gray-900">
                Upload Image
            </h2>

            <div className="space-y-4">
                {/* File input */}
                <div className="relative">
                    <input
                        ref={fileInputRef}
                        type="file"
                        accept={ALLOWED_TYPES.join(",")}
                        onChange={handleFileChange}
                        disabled={uploadState === "uploading"}
                        className="block w-full cursor-pointer rounded-lg border border-gray-300 bg-gray-50 px-3 py-2 text-sm text-gray-900 file:mr-4 file:rounded file:border-0 file:bg-blue-500 file:px-3 file:py-2 file:text-sm file:font-semibold file:text-white hover:bg-gray-100 disabled:cursor-not-allowed disabled:opacity-50"
                    />
                </div>

                {/* File name display */}
                {fileName && (
                    <p className="text-sm text-gray-600">
                        Selected:{" "}
                        <span className="font-medium">{fileName}</span>
                    </p>
                )}

                {/* Status messages */}
                {uploadState === "uploading" && (
                    <div className="flex items-center space-x-2 text-blue-600">
                        <Spinner />
                        <span className="text-sm">Uploading...</span>
                    </div>
                )}

                {uploadState === "success" && (
                    <div className="rounded-lg bg-green-50 p-3" role="status">
                        <p className="text-sm font-medium text-green-800">
                            ✓ Image uploaded successfully
                        </p>
                    </div>
                )}

                {uploadState === "error" && (
                    <div className="rounded-lg bg-red-50 p-3" role="alert">
                        <p className="text-sm font-medium text-red-800">
                            ✗ {errorMessage}
                        </p>
                    </div>
                )}

                {/* Supported formats info */}
                <div className="rounded-lg bg-gray-50 p-3">
                    <p className="text-xs text-gray-600">
                        Supported formats: PNG, JPEG, TIFF
                    </p>
                </div>
            </div>
        </div>
    );
}
