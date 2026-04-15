function traversePath(
    obj: unknown,
    path: string,
    depth: number,
    operation: "read" | "set"
) {
    const keys = path.split(".");
    let current: unknown = obj;

    for (let i = 0; i < depth; i++) {
        const key = keys[i];
        if (key === undefined) {
            throw new Error(`Invalid nested path: ${path}`);
        }

        if (typeof current !== "object" || current === null) {
            throw new Error(
                `Cannot ${operation} nested value at path: ${path}. ${key} is not an object.`
            );
        }

        const currentRecord = current as Record<string, unknown>;
        if (!(key in currentRecord)) {
            throw new Error(
                `Cannot ${operation} nested value at path: ${path}. Missing key: ${key}.`
            );
        }

        current = currentRecord[key];
    }

    return { current, keys };
}

export function getNestedValue(obj: any, path: string) {
    const keys = path.split(".");
    const { current } = traversePath(obj, path, keys.length, "read");
    return current;
}

export function setNestedValue(obj: any, path: string, value: unknown) {
    const { current, keys } = traversePath(
        obj,
        path,
        path.split(".").length - 1,
        "set"
    );

    if (typeof current !== "object" || current === null) {
        throw new Error(
            `Cannot set nested value at path: ${path}. Parent is not an object.`
        );
    }

    const parent = current as Record<string, unknown>;

    const lastKey = keys[keys.length - 1];
    if (lastKey === undefined) {
        throw new Error(
            `Invalid Nested Value (Last Key): ${lastKey} within ${path}`
        );
    }
    parent[lastKey] = value;
}
