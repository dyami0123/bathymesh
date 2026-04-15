import type { ConfigField } from "./configFormGenerator";
import { generateConfigComponents } from "./configFormGenerator";

function PostProcessingAdvancedConfig() {
    const postProcessingAdvancedFields: ConfigField[] = [
        {
            path: "mesh_generation.post_processing.remove_degenerate_triangles",
            label: "Remove Degenerate Triangles",
            kind: "checkbox",
            description: "Remove degenerate triangles",
        },
        {
            path: "mesh_generation.post_processing.remove_duplicated_vertices",
            label: "Remove Duplicated Vertices",
            kind: "checkbox",
            description: "Remove duplicated vertices",
        },
        {
            path: "mesh_generation.post_processing.remove_duplicated_triangles",
            label: "Remove Duplicated Triangles",
            kind: "checkbox",
            description: "Remove duplicated triangles",
        },
        {
            path: "mesh_generation.post_processing.remove_unreferenced_vertices",
            label: "Remove Unreferenced Vertices",
            kind: "checkbox",
            description: "Remove unreferenced vertices",
        },
        {
            path: "mesh_generation.post_processing.merge_close_vertices",
            label: "Merge Close Vertices",
            kind: "checkbox",
            description: "Merge vertices that are very close",
        },
        {
            path: "mesh_generation.post_processing.merge_vertices_threshold",
            label: "Merge Vertices Threshold",
            kind: "number",
            description: "Distance threshold for merging vertices",
            min: 0,
            step: 0.000001,
        },
        {
            path: "mesh_generation.post_processing.simplification_method",
            label: "Simplification Method",
            kind: "text",
            description: "Method for mesh simplification",
        },
        {
            path: "mesh_generation.post_processing.target_triangle_count",
            label: "Target Triangle Count",
            kind: "number",
            description: "Target triangle count for mesh simplification",
            min: 1,
            step: 1,
        },
        {
            path: "mesh_generation.post_processing.voxel_size",
            label: "Voxel Size",
            kind: "number",
            description: "Voxel size for vertex clustering simplification",
            min: 0,
            step: 0.001,
        },
    ];

    return generateConfigComponents(postProcessingAdvancedFields);
}

export function PostProcessingConfig() {
    const simplePostProcessingFields: ConfigField[] = [
        {
            path: "mesh_generation.post_processing.apply_post_processing",
            label: "Apply Post Processing",
            kind: "checkbox",
        },
    ];

    return (
        <div>
            {generateConfigComponents(simplePostProcessingFields)}

            <details>
                <summary>Advanced Options</summary>
                <PostProcessingAdvancedConfig />
            </details>
        </div>
    );
}
