import { createContext, useContext } from "react";
import type { ColorPickerState, ColorPickerAction } from "./colorPickerReducer";

const ColorPickerStateContext = createContext<ColorPickerState | null>(null);
const ColorPickerDispatchContext =
    createContext<React.Dispatch<ColorPickerAction> | null>(null);

export { ColorPickerStateContext, ColorPickerDispatchContext };

export function useColorPicker(): ColorPickerState {
    const ctx = useContext(ColorPickerStateContext);
    if (!ctx)
        throw new Error(
            "useColorPicker must be used inside ColormapStateProvider"
        );
    return ctx;
}

export function useColorPickerDispatch(): React.Dispatch<ColorPickerAction> {
    const ctx = useContext(ColorPickerDispatchContext);
    if (!ctx)
        throw new Error(
            "useColorPickerDispatch must be used inside ColormapStateProvider"
        );
    return ctx;
}
