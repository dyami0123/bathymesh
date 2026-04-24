import { useReducer } from "react";
import { viewerReducer, VIEWER_INITIAL_STATE } from "./viewerReducer";
import { ViewerStateContext, ViewerDispatchContext } from "./viewerContext";
export function ViewerStateProvider({
    children,
}: {
    children: React.ReactNode;
}) {
    // Viewer state
    const [viewerState, viewerDispatch] = useReducer(
        viewerReducer,
        VIEWER_INITIAL_STATE
    );
    return (
        <ViewerStateContext.Provider value={viewerState}>
            <ViewerDispatchContext.Provider value={viewerDispatch}>
                {children}
            </ViewerDispatchContext.Provider>
        </ViewerStateContext.Provider>
    );
}
