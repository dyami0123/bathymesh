import type { ImageData, HeightmapDataJson } from "@/client";

export type ViewerState = {
    activeImageData: ImageData | null;
    activeHeightmapData: HeightmapDataJson | null;
    refreshSignal: number;
    isLoading: boolean;
};

export const VIEWER_INITIAL_STATE: ViewerState = {
    activeImageData: null,
    activeHeightmapData: null,
    refreshSignal: 0,
    isLoading: true,
};

export type ViewerAction =
    | { type: "set_image"; data: ImageData | null }
    | { type: "set_heightmap"; data: HeightmapDataJson | null }
    | { type: "refresh" }
    | { type: "set_loading"; value: boolean }
    | { type: "reset" };

export function viewerReducer(
    state: ViewerState,
    action: ViewerAction
): ViewerState {
    switch (action.type) {
        case "set_image":
            return { ...state, activeImageData: action.data };
        case "set_heightmap":
            return { ...state, activeHeightmapData: action.data };
        case "refresh":
            return { ...state, refreshSignal: state.refreshSignal + 1 };
        case "set_loading":
            return { ...state, isLoading: action.value };
        case "reset":
            return VIEWER_INITIAL_STATE;
    }
}
