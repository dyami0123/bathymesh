import { cn } from "@/lib/cn";
import { button, badge } from "@/components/ui/styles";
import { Spinner } from "./Spinner";

type MeshControlsProps = {
    isLoading: boolean;
    isMeshVisible: boolean;
    hasError: boolean;
    errorMessage?: string;
    onCalculate: () => void;
    onView: () => void;
    onClear: () => void;
};

export function MeshControls({
    isLoading,
    isMeshVisible,
    hasError,
    errorMessage,
    onCalculate,
    onView,
    onClear,
}: MeshControlsProps) {
    return (
        <div className="flex items-center gap-2">
            <button
                type="button"
                onClick={onCalculate}
                disabled={isLoading}
                className={cn(button({ intent: "primary" }), "gap-2")}
            >
                {isLoading ? <Spinner /> : null}
                <span>{isLoading ? "Calculating..." : "Calculate Mesh"}</span>
            </button>

            <button
                type="button"
                onClick={onView}
                disabled={isLoading || isMeshVisible}
                className={cn(
                    button({ intent: isMeshVisible ? "success" : "ghost" })
                )}
            >
                {isMeshVisible ? "Mesh Loaded" : "View Mesh"}
            </button>

            <button
                type="button"
                onClick={onClear}
                disabled={!isMeshVisible}
                className={cn(button({ intent: "ghost" }))}
            >
                Clear Mesh
            </button>

            {hasError && errorMessage && (
                <div className={cn(badge({ intent: "error-pill" }))}>
                    {errorMessage}
                </div>
            )}
        </div>
    );
}
