import { useProject } from "@/state/projectContext";
import { useState, useEffect, useRef } from "react";
import {
    // calculateProjectContoursApiContoursProjectIdPost,
    calculateProjectHeightmapApiHeightmapProjectIdPost,
} from "@/client";
import { JobSubmitButton } from "./jobSubmitter";

type JobType = "calculate_heightmap" | "generate_mesh";

export function Runner() {
    return (
        <JobSubmitButton
            endpoints={{
                calculate_heightmap:
                    calculateProjectHeightmapApiHeightmapProjectIdPost,
                // generate_mesh: calculateProjectMeshApiMeshProjectIdPost,
            }}
            body={{ is_preview: false }}
        />
    );
}
