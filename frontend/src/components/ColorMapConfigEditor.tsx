import { useEffect, useMemo, useRef, useState } from "react";
import { useProject, useProjectDispatch } from "@/state/projectContext";
import {
    useColorPicker,
    useColorPickerDispatch,
} from "@/state/colorPickerContext";
import { useOnColorMapChanged } from "@/state/ColormapStateProvider";
import { ColorPicker } from "./ColorPicker";

type ColorMapEntry = {
    value: number;
    fuzziness: number;
};

type PickTarget = { type: "new" } | { type: "existing"; color: string };

function parseColorMap(
    colorMap: Record<string, unknown>,
    fallbackFuzziness: number
): Array<{ color: string; entry: ColorMapEntry }> {
    return Object.entries(colorMap)
        .map(([color, raw]) => {
            if (typeof raw !== "object" || raw === null) {
                return null;
            }

            const rawValue = (raw as Record<string, unknown>).value;
            const rawFuzziness = (raw as Record<string, unknown>).fuzziness;
            const value =
                typeof rawValue === "number" && Number.isFinite(rawValue)
                    ? rawValue
                    : 0;
            const fuzziness =
                typeof rawFuzziness === "number" &&
                Number.isFinite(rawFuzziness)
                    ? rawFuzziness
                    : fallbackFuzziness;

            return {
                color,
                entry: {
                    value,
                    fuzziness,
                },
            };
        })
        .filter((entry): entry is { color: string; entry: ColorMapEntry } => {
            return entry !== null;
        })
        .sort((a, b) => b.entry.value - a.entry.value);
}

export function ColorMapConfigEditor() {
    const project = useProject();
    const dispatch = useProjectDispatch();

    const { pickedColor } = useColorPicker();
    const colorPickerDispatch = useColorPickerDispatch();
    const onColorMapChanged = useOnColorMapChanged();

    const [newColor, setNewColor] = useState("#2d7f5e");
    const [newValue, setNewValue] = useState(0);
    const [newFuzziness, setNewFuzziness] = useState(
        project.image_processing.default_fuzziness
    );
    const [addError, setAddError] = useState<string | null>(null);
    const [pickTarget, setPickTarget] = useState<PickTarget | null>(null);
    const pickTargetRef = useRef<PickTarget | null>(null);

    useEffect(() => {
        colorPickerDispatch({
            type: "set_picking",
            value: pickTarget !== null,
        });
    }, [pickTarget, colorPickerDispatch]);

    const entries = useMemo(
        () =>
            parseColorMap(
                project.image_processing.color_map as Record<string, unknown>,
                project.image_processing.default_fuzziness
            ),
        [
            project.image_processing.color_map,
            project.image_processing.default_fuzziness,
        ]
    );

    const hasExistingColor = (color: string) =>
        entries.some((entry) => entry.color === color);

    const togglePickTarget = (target: PickTarget) => {
        const isActive =
            pickTarget !== null &&
            pickTarget.type === target.type &&
            (target.type === "new" ||
                (pickTarget.type === "existing" &&
                    target.type === "existing" &&
                    pickTarget.color === target.color));
        const next = isActive ? null : target;
        setPickTarget(next);
        pickTargetRef.current = next;
    };

    const isPickTargetActive = (target: PickTarget): boolean => {
        if (!pickTarget) return false;
        if (target.type === "new" && pickTarget.type === "new") return true;
        if (target.type === "existing" && pickTarget.type === "existing") {
            return target.color === pickTarget.color;
        }
        return false;
    };

    useEffect(() => {
        if (pickedColor) {
            const target = pickTargetRef.current;
            console.debug(
                "[color-pick] ColorMapConfigEditor received pickedColor",
                pickedColor,
                "target:",
                target
            );
            if (target?.type === "existing") {
                if (
                    pickedColor !== target.color &&
                    !hasExistingColor(pickedColor)
                ) {
                    dispatch({
                        type: "rename_color_map",
                        oldColor: target.color,
                        newColor: pickedColor,
                    });
                    onColorMapChanged();
                } else {
                    console.debug(
                        "[color-pick] Skipped: color already exists or unchanged"
                    );
                }
            } else {
                setNewColor(pickedColor);
            }
            setPickTarget(null);
            pickTargetRef.current = null;
            colorPickerDispatch({ type: "consume_picked_color" });
        }
    }, [pickedColor, colorPickerDispatch]);

    const addEntry = () => {
        if (hasExistingColor(newColor)) {
            setAddError(`Color ${newColor} already exists in the map.`);
            return;
        }

        dispatch({
            type: "update_color_map",
            color: newColor,
            value: newValue,
            fuzziness: newFuzziness,
        });
        onColorMapChanged();
        setAddError(null);
    };

    return (
        <section className="rounded-lg border border-gray-300 bg-white p-4 shadow-sm">
            <div className="mb-3 flex items-center justify-between">
                <h2 className="text-lg font-semibold text-gray-900">
                    Colormap Editor
                </h2>
                <span className="text-xs text-gray-500">
                    Changes sync to backend automatically
                </span>
            </div>

            {entries.length === 0 ? (
                <p className="mb-3 rounded bg-gray-50 px-3 py-2 text-sm text-gray-600">
                    No color mappings yet. Add one below.
                </p>
            ) : null}

            <div className="space-y-2">
                {entries.map(({ color, entry }) => (
                    <div
                        key={color}
                        className="grid grid-cols-1 gap-2 rounded border border-gray-200 p-3 md:grid-cols-[1fr_1fr_1fr_auto] md:items-center"
                    >
                        <div>
                            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">
                                Color
                            </label>
                            <div className="flex items-center gap-1">
                                <ColorPicker
                                    value={color}
                                    onChange={(nextColor) => {
                                        if (
                                            nextColor !== color &&
                                            hasExistingColor(nextColor)
                                        ) {
                                            return;
                                        }
                                        dispatch({
                                            type: "rename_color_map",
                                            oldColor: color,
                                            newColor: nextColor,
                                        });
                                    }}
                                    onCommit={() => onColorMapChanged()}
                                />
                                <button
                                    type="button"
                                    onClick={() =>
                                        togglePickTarget({
                                            type: "existing",
                                            color,
                                        })
                                    }
                                    className={`self-end rounded border px-2 py-1.5 text-xs font-medium transition-colors ${
                                        isPickTargetActive({
                                            type: "existing",
                                            color,
                                        })
                                            ? "border-blue-500 bg-blue-100 text-blue-700"
                                            : "border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
                                    }`}
                                    title="Pick color from mesh"
                                >
                                    Pick
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">
                                Value
                            </label>
                            <input
                                type="number"
                                value={entry.value}
                                onChange={(event) => {
                                    dispatch({
                                        type: "update_color_map",
                                        color,
                                        value: Number(event.target.value),
                                        fuzziness: entry.fuzziness,
                                    });
                                    onColorMapChanged();
                                }}
                                step={0.01}
                                className="w-full rounded border border-gray-300 px-2 py-1 text-sm text-black"
                            />
                        </div>

                        <div>
                            <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">
                                Fuzziness
                            </label>
                            <input
                                type="number"
                                value={entry.fuzziness}
                                onChange={(event) => {
                                    dispatch({
                                        type: "update_color_map",
                                        color,
                                        value: entry.value,
                                        fuzziness: Number(event.target.value),
                                    });
                                    onColorMapChanged();
                                }}
                                step={0.1}
                                min={0}
                                className="w-full rounded border border-gray-300 px-2 py-1 text-sm text-black"
                            />
                        </div>

                        <div className="self-end md:self-center">
                            <button
                                type="button"
                                onClick={() => {
                                    dispatch({
                                        type: "remove_color_map",
                                        color,
                                    });
                                    onColorMapChanged();
                                }}
                                className="w-full rounded border border-red-200 bg-red-50 px-3 py-1 text-sm font-medium text-red-700 hover:bg-red-100 md:w-auto"
                            >
                                Remove
                            </button>
                        </div>
                    </div>
                ))}
            </div>

            <div className="mt-4 rounded border border-gray-200 bg-gray-50 p-3">
                <h3 className="mb-2 text-sm font-semibold text-gray-900">
                    Add Color Mapping
                </h3>
                <div className="grid grid-cols-1 gap-2 md:grid-cols-[1fr_1fr_1fr_auto] md:items-end">
                    <div>
                        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">
                            Color
                        </label>
                        <div className="flex items-center gap-1">
                            <ColorPicker
                                value={newColor}
                                onChange={setNewColor}
                            />
                            <button
                                type="button"
                                onClick={() =>
                                    togglePickTarget({ type: "new" })
                                }
                                className={`self-end rounded border px-2 py-1.5 text-xs font-medium transition-colors ${
                                    isPickTargetActive({ type: "new" })
                                        ? "border-blue-500 bg-blue-100 text-blue-700"
                                        : "border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
                                }`}
                                title="Pick color from mesh"
                            >
                                Pick
                            </button>
                        </div>
                    </div>

                    <div>
                        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">
                            Value
                        </label>
                        <input
                            type="number"
                            value={newValue}
                            onChange={(event) =>
                                setNewValue(Number(event.target.value))
                            }
                            step={0.01}
                            className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
                        />
                    </div>

                    <div>
                        <label className="mb-1 block text-xs font-medium uppercase tracking-wide text-gray-500">
                            Fuzziness
                        </label>
                        <input
                            type="number"
                            value={newFuzziness}
                            onChange={(event) =>
                                setNewFuzziness(Number(event.target.value))
                            }
                            step={0.1}
                            min={0}
                            className="w-full rounded border border-gray-300 px-2 py-1 text-sm"
                        />
                    </div>

                    <button
                        type="button"
                        onClick={addEntry}
                        className="rounded bg-gray-900 px-4 py-2 text-sm font-semibold text-white hover:bg-gray-800"
                    >
                        Add
                    </button>
                </div>
                {addError ? (
                    <p className="mt-2 text-sm text-red-600">{addError}</p>
                ) : null}
            </div>
        </section>
    );
}
