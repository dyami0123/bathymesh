import { useProject, useProjectDispatch } from "@/state/projectContext";
import { getNestedValue } from "@/utilites";

export type ConfigField = {
    path: string;
    label: string;
    kind: "number" | "text" | "checkbox" | "select";
    description?: string;
    tooltip?: string;
    className?: string;
    min?: number;
    max?: number;
    step?: number;
    options?: { label: string; value: string | number }[];
};

function parseValue(
    kind: ConfigField["kind"],
    e: React.ChangeEvent<HTMLInputElement>
) {
    if (kind === "checkbox") return e.target.checked;
    if (kind === "number") return Number(e.target.value);
    return e.target.value;
}

function ConfigFieldInput({ field }: { field: ConfigField }) {
    const project = useProject();
    const dispatch = useProjectDispatch();

    const value = getNestedValue(project, field.path);

    if (field.kind === "checkbox") {
        return (
            <label className={field.className}>
                {field.label}
                <input
                    type="checkbox"
                    checked={Boolean(value)}
                    onChange={(e) =>
                        dispatch({
                            type: "set_by_path",
                            path: field.path,
                            value: parseValue(field.kind, e),
                        })
                    }
                    title={field.tooltip}
                />
            </label>
        );
    }

    return (
        <label className={field.className}>
            {field.label}
            <input
                type={field.kind}
                value={(value as number) ?? ""}
                onChange={(e) =>
                    dispatch({
                        type: "set_by_path",
                        path: field.path,
                        value: parseValue(field.kind, e),
                    })
                }
                title={field.tooltip ?? field.description}
                min={field.min}
                max={field.max}
                step={field.step}
                className="ml-2 p-1 border rounded"
            />
        </label>
    );
}

export function generateConfigComponents(fields: ConfigField[]) {
    // validate paths on build
    const project = useProject();
    fields.map((field) => {
        getNestedValue(project, field.path);
    });

    return (
        <div className="flex flex-col gap-4">
            <h2 className="text-lg font-bold">Contour Extraction Options</h2>
            <div className="flex flex-col gap-2">
                {fields.map((field) => (
                    <ConfigFieldInput key={field.path} field={field} />
                ))}
            </div>
        </div>
    );
}
