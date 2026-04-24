import { createContext, useContext } from "react";
import type { ViewerState, ViewerAction } from "./viewerReducer";

const ViewerStateContext = createContext<ViewerState | null>(null);
const ViewerDispatchContext =
    createContext<React.Dispatch<ViewerAction> | null>(null);

export { ViewerStateContext, ViewerDispatchContext };

export function useViewer(): ViewerState {
    const ctx = useContext(ViewerStateContext);
    if (!ctx)
        throw new Error("useViewer must be used inside ViewerStateProvider");
    return ctx;
}

export function useViewerDispatch(): React.Dispatch<ViewerAction> {
    const ctx = useContext(ViewerDispatchContext);
    if (!ctx)
        throw new Error(
            "useViewerDispatch must be used inside ViewerStateProvider"
        );
    return ctx;
}
