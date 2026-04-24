import type { ProjectConfigOutput } from "../client";
import { produce } from "immer";
import { setNestedValue } from "@/utilites";

export type Action =
    | { type: "set_project"; payload: ProjectConfigOutput }
    | { type: "set_by_path"; path: string; value: unknown }
    | {
          type: "update_color_map";
          color: string;
          value: number;
          fuzziness: number;
      }
    | { type: "remove_color_map"; color: string }
    | {
          type: "rename_color_map";
          oldColor: string;
          newColor: string;
      };

export function projectReducer(
    state: ProjectConfigOutput,
    action: Action
): ProjectConfigOutput {
    return produce(state, (draft) => {
        switch (action.type) {
            case "set_project":
                return action.payload;

            case "set_by_path": {
                setNestedValue(draft, action.path, action.value);
                return;
            }

            case "update_color_map":
                draft.image_processing.color_map[action.color] = {
                    value: action.value,
                    fuzziness: action.fuzziness,
                };
                return;

            case "remove_color_map":
                delete draft.image_processing.color_map[action.color];
                return;

            case "rename_color_map": {
                const originalEntry =
                    draft.image_processing.color_map[action.oldColor];
                if (
                    originalEntry === undefined ||
                    action.oldColor === action.newColor
                ) {
                    return;
                }

                delete draft.image_processing.color_map[action.oldColor];
                draft.image_processing.color_map[action.newColor] =
                    originalEntry;
                return;
            }
        }
    });
}
