import type { ImageData } from "@/types/imageData";

export function extractImageBlob(payload: unknown): Blob | null {
    if (payload instanceof Blob || payload instanceof File) {
        return payload;
    }

    if (payload && typeof payload === "object" && "data" in payload) {
        const nested = (payload as { data?: unknown }).data;
        if (nested instanceof Blob || nested instanceof File) {
            return nested;
        }
    }

    return null;
}

export async function loadBitmapFromBlob(blob: Blob): Promise<ImageBitmap> {
    if (typeof createImageBitmap !== "function") {
        throw new Error("createImageBitmap is not available in this browser.");
    }
    return createImageBitmap(blob);
}

export async function buildImageColorArray(
    blob: Blob,
    rows: number,
    cols: number
): Promise<Float32Array | null> {
    if (rows === 0 || cols === 0) return null;

    const bitmap = await loadBitmapFromBlob(blob);

    try {
        const canvas = document.createElement("canvas");
        canvas.width = bitmap.width;
        canvas.height = bitmap.height;

        const ctx = canvas.getContext("2d", { willReadFrequently: true });
        if (!ctx) return null;

        ctx.drawImage(bitmap, 0, 0);
        const pixels = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
        const colors = new Float32Array(rows * cols * 3);

        for (let r = 0; r < rows; r++) {
            const v = rows === 1 ? 0 : r / (rows - 1);
            const y = Math.round(v * (canvas.height - 1));

            for (let c = 0; c < cols; c++) {
                const u = cols === 1 ? 0 : c / (cols - 1);
                const x = Math.round(u * (canvas.width - 1));
                const pixelIndex = (y * canvas.width + x) * 4;
                const colorIndex = (r * cols + c) * 3;

                colors[colorIndex + 0] = (pixels[pixelIndex + 0] ?? 0) / 255;
                colors[colorIndex + 1] = (pixels[pixelIndex + 1] ?? 0) / 255;
                colors[colorIndex + 2] = (pixels[pixelIndex + 2] ?? 0) / 255;
            }
        }

        return colors;
    } finally {
        bitmap.close();
    }
}

export async function getImageColorsFromBlob(
    grid: number[][],
    imageData: ImageData
): Promise<Float32Array | null> {
    let imageColors: Float32Array | null = null;
    try {
        const imageBlob = extractImageBlob(imageData.data);
        if (imageBlob) {
            imageColors = await buildImageColorArray(
                imageBlob,
                grid.length,
                grid[0]?.length ?? 0
            );
        }
    } catch (imageError) {
        console.warn("Failed to build image-based colors:", imageError);
    }

    return imageColors;
}
