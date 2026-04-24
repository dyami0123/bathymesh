import { useEffect, useMemo, useState } from "react";

function normalizeHexColor(value: string): string | null {
    const input = value.trim().toLowerCase();

    const shortHexMatch = /^#([0-9a-f]{3})$/i.exec(input);
    if (shortHexMatch?.[1]) {
        const [r, g, b] = shortHexMatch[1].split("");
        return `#${r}${r}${g}${g}${b}${b}`;
    }

    const fullHexMatch = /^#([0-9a-f]{6})$/i.exec(input);
    if (fullHexMatch?.[0]) {
        return fullHexMatch[0].toLowerCase();
    }

    return null;
}

export function ColorPicker({
    value,
    onChange,
    onCommit,
    disabled = false,
}: {
    value: string;
    onChange: (nextValue: string) => void;
    onCommit?: () => void;
    disabled?: boolean;
}) {
    const [hasUncommittedChange, setHasUncommittedChange] = useState(false);
    const normalizedValue = useMemo(
        () => normalizeHexColor(value) ?? "#000000",
        [value]
    );
    const [draftColor, setDraftColor] = useState(normalizedValue);

    useEffect(() => {
        if (!hasUncommittedChange) {
            setDraftColor(normalizedValue);
        }
    }, [normalizedValue, hasUncommittedChange]);

    const commitDraftColor = () => {
        if (!hasUncommittedChange) {
            return;
        }

        if (draftColor !== normalizedValue) {
            onChange(draftColor);
        }

        onCommit?.();
        setHasUncommittedChange(false);
    };

    return (
        <div className="flex items-center gap-2">
            <input
                type="color"
                value={draftColor}
                onChange={(event) => {
                    const nextColor = normalizeHexColor(
                        event.target.value.toLowerCase()
                    );
                    if (nextColor) {
                        setDraftColor(nextColor);
                        setHasUncommittedChange(true);
                    }
                }}
                onBlur={commitDraftColor}
                disabled={disabled}
                className="h-9 w-12 cursor-pointer rounded border border-gray-300 bg-white p-1 disabled:cursor-not-allowed disabled:opacity-60"
                aria-label="Pick color"
            />
            <input
                type="text"
                value={draftColor}
                onChange={(event) => {
                    const nextColor = normalizeHexColor(event.target.value);
                    if (nextColor) {
                        setDraftColor(nextColor);
                        setHasUncommittedChange(true);
                    }
                }}
                onBlur={commitDraftColor}
                onKeyDown={(event) => {
                    if (event.key === "Enter") {
                        commitDraftColor();
                    }
                }}
                disabled={disabled}
                className="w-24 rounded border border-gray-300 px-2 py-1 text-sm text-gray-900 disabled:cursor-not-allowed disabled:bg-gray-100"
                aria-label="Hex color"
            />
        </div>
    );
}
