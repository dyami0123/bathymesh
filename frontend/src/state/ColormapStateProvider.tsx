import {
    createContext,
    useCallback,
    useContext,
    useEffect,
    useReducer,
    useRef,
} from "react";
import { calculateProjectHeightmapApiHeightmapProjectIdPost } from "@/client";
import { useViewerDispatch } from "./viewerContext";
import {
    colorPickerReducer,
    COLOR_PICKER_INITIAL_STATE,
} from "./colorPickerReducer";
import {
    ColorPickerStateContext,
    ColorPickerDispatchContext,
} from "./colorPickerContext";
import { useProject } from "./projectContext";
import { blockingApiCall } from "@/blockingApiCall";
import { PREVIEW_DIM } from "@/components/HeightmapViewer";

const ColorMapChangedContext = createContext<(() => void) | null>(null);

export function useOnColorMapChanged(): () => void {
    const ctx = useContext(ColorMapChangedContext);
    if (!ctx)
        throw new Error(
            "useOnColorMapChanged must be used inside ColormapStateProvider"
        );
    return ctx;
}

export function ColormapStateProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    // Viewer state
    const viewerDispatch = useViewerDispatch();
    const projectState = useProject();
    const [colorPickerState, colorPickerDispatch] = useReducer(
        colorPickerReducer,
        COLOR_PICKER_INITIAL_STATE
    );
    const colorMapDebounceRef = useRef<number | null>(null);

    const recomputePreviewFromColorMap = useCallback(
        async (projectId: string) => {
            viewerDispatch({ type: "set_loading", value: true });
            try {
                await blockingApiCall({
                    endpoint:
                        calculateProjectHeightmapApiHeightmapProjectIdPost,
                    project_id: projectId,
                    body: {
                        is_preview: true,
                        max_dimension_override: PREVIEW_DIM,
                    },
                });
                viewerDispatch({ type: "refresh" });
            } catch (error) {
                console.error(
                    "Failed to recompute preview heightmap from colormap changes",
                    error
                );
                viewerDispatch({ type: "set_loading", value: false });
            }
        },
        []
    );

    const handleColorMapChanged = useCallback(() => {
        if (!projectState.project_id) return;

        if (colorMapDebounceRef.current !== null) {
            window.clearTimeout(colorMapDebounceRef.current);
        }

        colorMapDebounceRef.current = window.setTimeout(() => {
            void recomputePreviewFromColorMap(projectState.project_id);
        }, 1000);
    }, [recomputePreviewFromColorMap, projectState.project_id]);

    useEffect(() => {
        return () => {
            if (colorMapDebounceRef.current !== null) {
                window.clearTimeout(colorMapDebounceRef.current);
            }
        };
    }, []);

    return (
        <ColorPickerStateContext.Provider value={colorPickerState}>
            <ColorPickerDispatchContext.Provider value={colorPickerDispatch}>
                <ColorMapChangedContext.Provider value={handleColorMapChanged}>
                    {children}
                </ColorMapChangedContext.Provider>
            </ColorPickerDispatchContext.Provider>
        </ColorPickerStateContext.Provider>
    );
}
