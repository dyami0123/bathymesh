import type { ProjectConfigOutput } from "../client";
import { produce } from "immer";

export type Action =
  | { type: "set_project"; payload: ProjectConfigOutput }
  | { type: "set_stateless"; payload: boolean }
  | { type: "set_exterior_buffer_width"; payload: number }
  | {
      type: "update_color_map";
      color: string;
      value: number;
      fuzziness: number;
    };

export function projectReducer(
  state: ProjectConfigOutput,
  action: Action
): ProjectConfigOutput {
  return produce(state, (draft) => {
    switch (action.type) {
      case "set_project":
        return action.payload;

      case "set_stateless":
        draft.mesh_generation.stateless = action.payload;
        return;

      case "set_exterior_buffer_width":
        draft.mesh_generation.heightmap_processing.exterior_buffer_width =
          action.payload;
        return;

      case "update_color_map":
        draft.image_processing.color_map[action.color] = {
          value: action.value,
          fuzziness: action.fuzziness,
        };
        return;
    }
  });
}
