import { useProjectSelectionState } from "@/state/projectContext";
import { label, select } from "./ui/styles";
import { cn } from "@/lib/cn";

type ProjectSelectorProps = {
    inPopup?: boolean;
};

export function ProjectSelector({ inPopup = false }: ProjectSelectorProps) {
    const { projectOptions, selectedProjectId, setSelectedProjectId } =
        useProjectSelectionState();

    return (
        <div className={cn("w-full", inPopup ? "max-w-xl" : "")}>
            <label htmlFor="selected-project" className={label()}>
                Selected Project
            </label>
            <select
                id="selected-project"
                value={selectedProjectId}
                onChange={(event) => setSelectedProjectId(event.target.value)}
                className={cn(select())}
            >
                {projectOptions.map((projectId) => (
                    <option key={projectId} value={projectId}>
                        {projectId}
                    </option>
                ))}
            </select>
        </div>
    );
}
