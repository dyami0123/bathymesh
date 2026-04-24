import { useEffect, useMemo, useState } from "react";
import { colorInput, input } from "@/components/ui/styles";
import { cn } from "@/lib/cn";

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
                className={colorInput()}
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
                className={cn(
                    input({ variant: "compact", width: "fixed" }),
                    "w-24"
                )}
                aria-label="Hex color"
            />
        </div>
    );
}
