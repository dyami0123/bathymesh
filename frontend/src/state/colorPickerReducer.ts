export type ColorPickerState = {
    pickedColor: string | null;
    isPickingColor: boolean;
};

export const COLOR_PICKER_INITIAL_STATE: ColorPickerState = {
    pickedColor: null,
    isPickingColor: false,
};

export type ColorPickerAction =
    | { type: "pick_color"; hex: string }
    | { type: "consume_picked_color" }
    | { type: "set_picking"; value: boolean }
    | { type: "reset" };

export function colorPickerReducer(
    state: ColorPickerState,
    action: ColorPickerAction
): ColorPickerState {
    switch (action.type) {
        case "pick_color":
            return { ...state, pickedColor: action.hex };
        case "consume_picked_color":
            return { ...state, pickedColor: null };
        case "set_picking":
            return { ...state, isPickingColor: action.value };
        case "reset":
            return COLOR_PICKER_INITIAL_STATE;
    }
}
