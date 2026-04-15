import type { ConfigField } from "./configFormGenerator";
import { generateConfigComponents } from "./configFormGenerator";

export function ContourOptions() {
    const contourFields: ConfigField[] = [
        {
            path: "mesh_generation.contour_extraction.min_polygon_area",
            label: "Min Polygon Area",
            kind: "number",
            description: "Minimum polygon area for contour extraction",
        },
        {
            path: "mesh_generation.contour_extraction.simplify_tolerance",
            label: "Simplify Tolerance",
            kind: "number",
            description: "Tolerance for contour simplification",
        },
        {
            path: "mesh_generation.contour_extraction.max_segments",
            label: "Max Segments",
            kind: "number",
            description: "Maximum number of contour segments",
            min: 1,
            step: 1,
        },
        {
            path: "mesh_generation.contour_extraction.min_area_fraction",
            label: "Min Area Fraction",
            kind: "number",
            description: "Minimum retained area fraction after filtering",
            min: 0,
            max: 1,
            step: 0.01,
        },
        {
            path: "mesh_generation.mesh_combination.merge_threshold",
            label: "Merge Threshold",
            kind: "number",
            description:
                "Threshold for merging close verticies when combining meshes",
            min: 0,
            max: 1,
            step: 0.01,
        },
    ];

    return generateConfigComponents(contourFields);
}
