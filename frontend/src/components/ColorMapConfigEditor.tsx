import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useProject, useProjectDispatch } from "@/state/projectContext";
import {
    useColorPicker,
    useColorPickerDispatch,
} from "@/state/colorPickerContext";
import { useOnColorMapChanged } from "@/state/ColormapStateProvider";
import { EyedropperIcon } from "./icons/EyedropperIcon";
import { Card } from "./ui/Card";
import { Heading } from "./ui/Heading";
import { Button } from "./ui/Button";
import { cn } from "@/lib/cn";
import { input } from "./ui/styles";

/** Minimum span for display range to prevent collapsing to a single point */
const DISPLAY_RANGE_MIN_SPAN = 0.01;

type ColorMapEntry = {
    value: number;
    fuzziness: number;
};

type PickTarget = { type: "new" } | { type: "existing"; color: string };

function parseDraftNumber(rawValue: string): number | null {
    const trimmed = rawValue.trim();
    if (trimmed === "") {
        return null;
    }

    const parsed = Number(trimmed);
    return Number.isFinite(parsed) ? parsed : null;
}

/** Parse and round to integer */
function parseDraftIntNumber(rawValue: string): number | null {
    const parsed = parseDraftNumber(rawValue);
    return parsed !== null ? Math.round(parsed) : null;
}

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
    const [maxFuzziness, setMaxFuzziness] = useState(10);
    const [pickTarget, setPickTarget] = useState<PickTarget | null>(null);
    const [draggingColor, setDraggingColor] = useState<string | null>(null);
    const pickTargetRef = useRef<PickTarget | null>(null);
    const railRef = useRef<HTMLDivElement | null>(null);
    const dragFrameRef = useRef<number | null>(null);
    const initializedDisplayRangeRef = useRef(false);

    // Sync pickTarget state with ref for access in effects
    useEffect(() => {
        pickTargetRef.current = pickTarget;
    }, [pickTarget]);

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

    const valueExtent = useMemo(() => {
        if (entries.length === 0) {
            return { min: 0, max: 0 };
        }

        const values = entries.map(({ entry }) => entry.value);
        return {
            min: Math.min(...values),
            max: Math.max(...values),
        };
    }, [entries]);

    const [displayRangeMin, setDisplayRangeMin] = useState(0);
    const [displayRangeMax, setDisplayRangeMax] = useState(1);
    const [displayRangeMinDraft, setDisplayRangeMinDraft] = useState("0");
    const [displayRangeMaxDraft, setDisplayRangeMaxDraft] = useState("1");
    const [maxFuzzinessDraft, setMaxFuzzinessDraft] = useState("10");

    useEffect(() => {
        if (entries.length === 0) {
            initializedDisplayRangeRef.current = false;
            setDisplayRangeMin(0);
            setDisplayRangeMax(1);
            return;
        }

        if (!initializedDisplayRangeRef.current) {
            initializedDisplayRangeRef.current = true;
            setDisplayRangeMin(valueExtent.min);
            setDisplayRangeMax(valueExtent.max);
            return;
        }

        setDisplayRangeMin((prev) => Math.min(prev, valueExtent.min));
        setDisplayRangeMax((prev) => Math.max(prev, valueExtent.max));
    }, [entries.length, valueExtent.min, valueExtent.max]);

    useEffect(() => {
        setDisplayRangeMaxDraft(displayRangeMax.toString());
    }, [displayRangeMax]);

    useEffect(() => {
        setDisplayRangeMinDraft(displayRangeMin.toString());
    }, [displayRangeMin]);

    useEffect(() => {
        setMaxFuzzinessDraft(maxFuzziness.toString());
    }, [maxFuzziness]);

    const entriesByColor = useMemo(() => {
        return new Map(entries.map(({ color, entry }) => [color, entry]));
    }, [entries]);

    const getMarkerTopPercent = (value: number): number => {
        if (displayRangeMax === displayRangeMin) {
            return 50;
        }
        return (
            ((displayRangeMax - value) / (displayRangeMax - displayRangeMin)) *
            100
        );
    };

    /** Check if a color already exists in the color map */
    const hasExistingColor = useCallback(
        (color: string) => entries.some((entry) => entry.color === color),
        [entries]
    );

    const updateColorValue = useCallback(
        (color: string, value: number) => {
            const existingEntry = entriesByColor.get(color);
            if (!existingEntry) {
                return;
            }

            dispatch({
                type: "update_color_map",
                color,
                value,
                fuzziness: existingEntry.fuzziness,
            });
        },
        [dispatch, entriesByColor]
    );

    const updateColorFuzziness = useCallback(
        (color: string, fuzziness: number) => {
            const existingEntry = entriesByColor.get(color);
            if (!existingEntry) {
                return;
            }

            const clampedFuzziness = Math.min(
                Math.max(fuzziness, 0),
                Math.max(maxFuzziness, 0)
            );

            dispatch({
                type: "update_color_map",
                color,
                value: existingEntry.value,
                fuzziness: clampedFuzziness,
            });
        },
        [dispatch, entriesByColor, maxFuzziness]
    );

    const updateDraggedColorFromClientY = useCallback(
        (color: string, clientY: number) => {
            const railElement = railRef.current;
            if (!railElement) {
                return;
            }

            const range = displayRangeMax - displayRangeMin;
            if (!Number.isFinite(range) || range <= 0) {
                updateColorValue(color, displayRangeMin);
                return;
            }

            const rect = railElement.getBoundingClientRect();
            const y = Math.min(Math.max(clientY, rect.top), rect.bottom);
            const ratio = (y - rect.top) / rect.height;
            const nextValue = displayRangeMax - ratio * range;

            // Snap to 0.1 increments
            const snappedValue = Math.round(nextValue * 10) / 10;
            updateColorValue(color, snappedValue);
        },
        [displayRangeMax, displayRangeMin, updateColorValue]
    );

    // Throttle drag updates with requestAnimationFrame
    useEffect(() => {
        if (!draggingColor) {
            return;
        }

        let lastClientY = 0;

        const handlePointerMove = (event: PointerEvent) => {
            lastClientY = event.clientY;
            if (dragFrameRef.current !== null) {
                return;
            }
            dragFrameRef.current = requestAnimationFrame(() => {
                updateDraggedColorFromClientY(draggingColor, lastClientY);
                dragFrameRef.current = null;
            });
        };

        const handlePointerUp = () => {
            if (dragFrameRef.current !== null) {
                cancelAnimationFrame(dragFrameRef.current);
                dragFrameRef.current = null;
            }
            setDraggingColor(null);
        };

        window.addEventListener("pointermove", handlePointerMove);
        window.addEventListener("pointerup", handlePointerUp);

        return () => {
            window.removeEventListener("pointermove", handlePointerMove);
            window.removeEventListener("pointerup", handlePointerUp);
            if (dragFrameRef.current !== null) {
                cancelAnimationFrame(dragFrameRef.current);
                dragFrameRef.current = null;
            }
        };
    }, [draggingColor, updateDraggedColorFromClientY]);

    const onChangeDisplayRangeMax = useCallback(
        (rawValue: number) => {
            if (!Number.isFinite(rawValue)) {
                return;
            }

            const clampedMax = Math.max(rawValue, valueExtent.max);
            // Enforce minimum span to prevent collapse
            const nextMax = Math.max(
                clampedMax,
                displayRangeMin + DISPLAY_RANGE_MIN_SPAN
            );
            setDisplayRangeMax(nextMax);
        },
        [displayRangeMin, valueExtent.max]
    );

    const onChangeDisplayRangeMin = useCallback(
        (rawValue: number) => {
            if (!Number.isFinite(rawValue)) {
                return;
            }

            const clampedMin = Math.min(rawValue, valueExtent.min);
            // Enforce minimum span to prevent collapse
            const nextMin = Math.min(
                clampedMin,
                displayRangeMax - DISPLAY_RANGE_MIN_SPAN
            );
            setDisplayRangeMin(nextMin);
        },
        [displayRangeMax, valueExtent.min]
    );

    const commitDisplayRangeMaxDraft = useCallback(() => {
        const parsed = parseDraftIntNumber(displayRangeMaxDraft);
        if (parsed === null) {
            setDisplayRangeMaxDraft(displayRangeMax.toString());
            return;
        }
        onChangeDisplayRangeMax(parsed);
    }, [displayRangeMaxDraft, displayRangeMax, onChangeDisplayRangeMax]);

    const commitDisplayRangeMinDraft = useCallback(() => {
        const parsed = parseDraftIntNumber(displayRangeMinDraft);
        if (parsed === null) {
            setDisplayRangeMinDraft(displayRangeMin.toString());
            return;
        }
        onChangeDisplayRangeMin(parsed);
    }, [displayRangeMinDraft, displayRangeMin, onChangeDisplayRangeMin]);

    const commitMaxFuzzinessDraft = useCallback(() => {
        const parsed = parseDraftIntNumber(maxFuzzinessDraft);
        if (parsed === null) {
            setMaxFuzzinessDraft(maxFuzziness.toString());
            return;
        }
        setMaxFuzziness(Math.max(parsed, 0));
    }, [maxFuzzinessDraft, maxFuzziness]);

    const getFuzzinessWidthPercent = (fuzziness: number): number => {
        const safeMax = Math.max(maxFuzziness, 0.0001);
        const ratio = Math.min(Math.max(fuzziness / safeMax, 0), 1);
        return 20 + ratio * 70;
    };

    /** Generate grid lines with nice intervals */
    const generateGridLines = (): Array<{ value: number; percent: number }> => {
        const range = displayRangeMax - displayRangeMin;
        if (range <= 0 || !Number.isFinite(range)) return [];

        const lines: Array<{ value: number; percent: number }> = [];

        // Determine interval size for grid (try to get 5-10 grid lines)
        let interval = 1;
        if (range <= 1) interval = 0.1;
        else if (range <= 5) interval = 0.5;
        else if (range <= 10) interval = 1;
        else if (range <= 20) interval = 2;
        else if (range <= 50) interval = 5;
        else interval = 10;

        // Start from a multiple of interval
        const startValue = Math.ceil(displayRangeMin / interval) * interval;

        for (
            let value = startValue;
            value <= displayRangeMax;
            value += interval
        ) {
            if (value >= displayRangeMin) {
                const percent = getMarkerTopPercent(value);
                lines.push({ value, percent });
            }
        }

        return lines;
    };

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
    };

    const isPickTargetActive = (target: PickTarget): boolean => {
        if (!pickTarget) return false;
        if (target.type === "new" && pickTarget.type === "new") return true;
        if (target.type === "existing" && pickTarget.type === "existing") {
            return target.color === pickTarget.color;
        }
        return false;
    };

    // Sync color map changes to backend when color map is updated
    useEffect(() => {
        onColorMapChanged();
    }, [project.image_processing.color_map, onColorMapChanged]);

    // Handle picked color with fixed dependencies
    useEffect(() => {
        if (pickedColor) {
            const target = pickTargetRef.current;
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
                }
            } else if (target?.type === "new") {
                setNewColor(pickedColor);
            }
            setPickTarget(null);
            colorPickerDispatch({ type: "consume_picked_color" });
        }
    }, [pickedColor, colorPickerDispatch, dispatch, hasExistingColor]);

    const addEntry = useCallback(() => {
        if (hasExistingColor(newColor)) {
            return;
        }

        dispatch({
            type: "update_color_map",
            color: newColor,
            value: 0,
            fuzziness: project.image_processing.default_fuzziness,
        });
    }, [
        dispatch,
        hasExistingColor,
        newColor,
        project.image_processing.default_fuzziness,
    ]);

    return (
        <div className="h-full overflow-y-auto">
            <label className="text-zinc-700">Color Editor</label>
            {entries.length === 0 ? (
                <p className="mb-3 rounded bg-gray-50 px-3 py-2 text-sm text-gray-600">
                    No color mappings yet. Add one below.
                </p>
            ) : null}

            <div className="flex items-stretch gap-3">
                <div className="w-full shrink-0 rounded border border-gray-200 bg-gray-50 px-2 py-2 min-h-100 max-h-[70vh]">
                    <div className="flex h-full flex-col items-center gap-2">
                        <div className="w-1/2 flex">
                            <label
                                htmlFor="max-height-input"
                                className="text-zinc-500 px-5"
                            >
                                Max Height
                            </label>
                            <input
                                id="max-height-input"
                                type="text"
                                inputMode="decimal"
                                value={displayRangeMaxDraft}
                                onChange={(event) =>
                                    setDisplayRangeMaxDraft(event.target.value)
                                }
                                onBlur={commitDisplayRangeMaxDraft}
                                onKeyDown={(event) => {
                                    if (event.key === "Enter") {
                                        event.currentTarget.blur();
                                    }
                                }}
                                className={input({ variant: "compact" })}
                                aria-label="Rail maximum value"
                            />
                        </div>

                        <div ref={railRef} className="relative w-full flex-1">
                            <div className="absolute inset-y-0 left-1/2 w-px -translate-x-1/2 bg-gray-300" />

                            {/* Grid lines and y-axis labels */}
                            {generateGridLines().map((gridLine) => (
                                <div
                                    key={`grid-${gridLine.value}`}
                                    className="absolute left-0 right-0 flex items-center"
                                    style={{ top: `${gridLine.percent}%` }}
                                >
                                    <div className="w-8 text-right pr-2 text-xs text-gray-400">
                                        {gridLine.value.toFixed(1)}
                                    </div>
                                    <div className="flex-1 h-px bg-gray-200" />
                                </div>
                            ))}

                            {entries.map(({ color, entry }) => (
                                <div
                                    key={`marker-${color}`}
                                    className="absolute left-1/2 -translate-x-1/2 -translate-y-1/2"
                                    style={{
                                        top: `${getMarkerTopPercent(entry.value)}%`,
                                    }}
                                >
                                    <div
                                        className="absolute left-1/2 top-1/2 h-0.5 -translate-x-1/2 -translate-y-1/2 rounded"
                                        style={{
                                            width: `${getFuzzinessWidthPercent(entry.fuzziness) * 5}%`,
                                            backgroundColor: color,
                                        }}
                                        aria-hidden="true"
                                    />

                                    <button
                                        type="button"
                                        className={cn(
                                            "relative z-10 h-3 w-3 rounded-full border border-white shadow",
                                            draggingColor === color
                                                ? "scale-125"
                                                : ""
                                        )}
                                        style={{
                                            backgroundColor: color,
                                        }}
                                        onPointerDown={(event) => {
                                            event.preventDefault();
                                            setDraggingColor(color);
                                            updateDraggedColorFromClientY(
                                                color,
                                                event.clientY
                                            );
                                        }}
                                        onWheel={(event) => {
                                            event.preventDefault();
                                            const direction =
                                                event.deltaY < 0 ? 1 : -1;
                                            updateColorFuzziness(
                                                color,
                                                entry.fuzziness + direction
                                            );
                                        }}
                                        title={`${color} (value: ${entry.value.toFixed(2)}, fuzziness: ${entry.fuzziness.toFixed(2)})`}
                                        aria-label={`Drag ${color} marker to change value; scroll to change fuzziness (current: value=${entry.value.toFixed(2)}, fuzziness=${entry.fuzziness.toFixed(2)})`}
                                    />

                                    <div
                                        className="
                                    absolute 
                                    left-full 
                                    top-1/2 z-20 
                                    ml-2 
                                    flex 
                                    -translate-y-1/2 
                                    items-center 
                                    gap-1 
                                    rounded-full 
                                    border 
                                    border-gray-200 
                                    bg-white p-1 
                                    shadow-sm"
                                        style={{ backgroundColor: color }}
                                    >
                                        <button
                                            type="button"
                                            onClick={() =>
                                                togglePickTarget({
                                                    type: "existing",
                                                    color,
                                                })
                                            }
                                            className={cn(
                                                "flex h-5 w-5 items-center justify-center rounded-full border transition-colors",
                                                isPickTargetActive({
                                                    type: "existing",
                                                    color,
                                                })
                                                    ? "border-blue-500 bg-blue-100 text-blue-700"
                                                    : "border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
                                            )}
                                            title="Pick color from mesh"
                                            aria-label={`Pick color from mesh for ${color}`}
                                        >
                                            <EyedropperIcon className="h-3 w-3" />
                                        </button>

                                        <button
                                            type="button"
                                            onClick={() => {
                                                dispatch({
                                                    type: "remove_color_map",
                                                    color,
                                                });
                                            }}
                                            className="flex h-5 w-5 items-center justify-center rounded-full border border-red-300 bg-white text-red-600 transition-colors hover:bg-red-50"
                                            title="Remove color mapping"
                                            aria-label={`Remove color mapping for ${color}`}
                                        >
                                            ×
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>

                        <div className="w-1/2 flex">
                            <label
                                htmlFor="min-height-input"
                                className="text-zinc-500 px-5"
                            >
                                Min Height
                            </label>
                            <input
                                id="min-height-input"
                                type="text"
                                inputMode="decimal"
                                value={displayRangeMinDraft}
                                onChange={(event) =>
                                    setDisplayRangeMinDraft(event.target.value)
                                }
                                onBlur={commitDisplayRangeMinDraft}
                                onKeyDown={(event) => {
                                    if (event.key === "Enter") {
                                        event.currentTarget.blur();
                                    }
                                }}
                                className={input({ variant: "compact" })}
                                aria-label="Rail minimum value"
                            />
                        </div>

                        <div className="w-1/2 flex">
                            <label
                                htmlFor="max-fuzziness-input"
                                className="text-zinc-500 px-5"
                            >
                                Max Fuzziness
                            </label>
                            <input
                                id="max-fuzziness-input"
                                type="text"
                                inputMode="decimal"
                                value={maxFuzzinessDraft}
                                onChange={(event) =>
                                    setMaxFuzzinessDraft(event.target.value)
                                }
                                onBlur={commitMaxFuzzinessDraft}
                                onKeyDown={(event) => {
                                    if (event.key === "Enter") {
                                        event.currentTarget.blur();
                                    }
                                }}
                                className={input({ variant: "compact" })}
                                aria-label="Maximum fuzziness"
                                title="Maximum fuzziness used for rail lines and mouse wheel adjustments"
                            />
                        </div>

                        <div className="flex items-center gap-2">
                            <Button
                                onClick={addEntry}
                                style={{
                                    backgroundColor: newColor,
                                }}
                            >
                                Add Color
                            </Button>
                            <button
                                type="button"
                                onClick={() =>
                                    togglePickTarget({
                                        type: "new",
                                    })
                                }
                                className={cn(
                                    "flex h-9 w-9 items-center justify-center rounded border transition-colors",
                                    isPickTargetActive({
                                        type: "new",
                                    })
                                        ? "border-blue-500 bg-blue-100 text-blue-700"
                                        : "border-gray-300 bg-white text-gray-600 hover:bg-gray-50"
                                )}
                                title="Pick color from mesh"
                                aria-label="Pick color from mesh for new color"
                            >
                                <EyedropperIcon className="h-4 w-4" />
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
