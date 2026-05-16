import { cva } from "class-variance-authority";

// ---------------------------------------------------------------------------
// Card / Section surface
// ---------------------------------------------------------------------------
export const card = cva("rounded-lg p-4", {
    variants: {
        variant: {
            default: "border border-gray-300 bg-white shadow-sm",
            inset: "border border-gray-200 bg-gray-50",
            dark: "border border-gray-700 bg-gray-900 text-gray-100",
        },
    },
    defaultVariants: { variant: "default" },
});

// ---------------------------------------------------------------------------
// Headings
// ---------------------------------------------------------------------------
export const heading = cva("font-semibold text-gray-900", {
    variants: {
        level: {
            section: "text-lg",
            subsection: "text-sm",
        },
    },
    defaultVariants: { level: "section" },
});

// ---------------------------------------------------------------------------
// Labels
// ---------------------------------------------------------------------------
export const label = cva("block font-medium", {
    variants: {
        variant: {
            default: "mb-2 text-sm text-gray-700",
            uppercase: "mb-1 text-xs uppercase tracking-wide text-gray-500",
        },
    },
    defaultVariants: { variant: "default" },
});

// ---------------------------------------------------------------------------
// Text input / number input
// ---------------------------------------------------------------------------
export const input = cva(
    "rounded " +
        "border " +
        "border-gray-300 " +
        "text-sm " +
        "text-gray-900 " +
        "disabled:cursor-not-allowed " +
        "disabled:bg-gray-100 " +
        "disabled:opacity-60",
    {
        variants: {
            variant: {
                default: "px-3 py-2",
                compact: "px-2 py-1",
            },
            width: {
                full: "w-full",
                fixed: "",
            },
        },
        defaultVariants: { variant: "default", width: "full" },
    }
);

// ---------------------------------------------------------------------------
// Select
// ---------------------------------------------------------------------------
export const select = cva(
    "w-full " +
        "rounded-full " +
        "border " +
        "border-gray-300 " +
        "px-3 " +
        "py-2 " +
        "text-sm " +
        "text-gray-900 " +
        "disabled:cursor-not-allowed " +
        "disabled:opacity-60"
);

// ---------------------------------------------------------------------------
// Buttons
// ---------------------------------------------------------------------------
export const button = cva(
    "inline-flex " +
        "items-center " +
        "justify-center " +
        "font-medium " +
        "transition " +
        "disabled:cursor-not-allowed " +
        "disabled:opacity-60",
    {
        variants: {
            intent: {
                primary: "bg-gray-900 " + "text-white " + "hover:bg-gray-800",
                secondary:
                    "border " +
                    "border-gray-300 " +
                    "bg-white " +
                    "text-gray-700 " +
                    "hover:bg-gray-50",
                danger:
                    "border " +
                    "border-red-200 " +
                    "bg-red-50 " +
                    "text-red-700 " +
                    "hover:bg-red-100",
                ghost: "bg-transparent text-gray-700 hover:bg-gray-100",
            },
            shape: {
                rounded: "rounded " + "px-4 " + "py-2 " + "text-sm",
                pill: "rounded-full " + "px-3 " + "py-1.5 " + "text-sm",
                compact: "rounded " + "px-3 " + "py-1 " + "text-sm",
            },
        },
        defaultVariants: { intent: "primary", shape: "rounded" },
    }
);

// ---------------------------------------------------------------------------
// Badge / status message
// ---------------------------------------------------------------------------
export const badge = cva("rounded-lg p-3 text-sm font-medium", {
    variants: {
        intent: {
            info: "bg-blue-50 " + "text-blue-700",
            success: "bg-green-50 " + "text-green-800",
            error: "bg-red-50 " + "text-red-800",
            muted: "bg-gray-50 " + "text-gray-600",
            "error-pill":
                "rounded-full " +
                "bg-red-50 " +
                "px-3 " +
                "py-1.5 " +
                "text-xs " +
                "text-red-600 " +
                "shadow-sm",
        },
    },
    defaultVariants: { intent: "muted" },
});

// ---------------------------------------------------------------------------
// File input
// ---------------------------------------------------------------------------
export const fileInput = cva(
    "block " +
        "w-full " +
        "cursor-pointer " +
        "rounded-lg " +
        "border " +
        "border-gray-300 " +
        "bg-gray-50 " +
        "px-3 " +
        "py-2 " +
        "text-sm " +
        "text-gray-900 " +
        "file:mr-4 " +
        "file:rounded " +
        "file:border-0 " +
        "file:bg-blue-500 " +
        "file:px-3 " +
        "file:py-2 " +
        "file:text-sm " +
        "file:font-semibold " +
        "file:text-white " +
        "hover:bg-gray-100 " +
        "disabled:cursor-not-allowed " +
        "disabled:opacity-50"
);

// ---------------------------------------------------------------------------
// Color-input (the native <input type="color">)
// ---------------------------------------------------------------------------
export const colorInput = cva(
    "h-9 " +
        "w-12 " +
        "cursor-pointer " +
        "rounded " +
        "border " +
        "border-gray-300 " +
        "bg-white " +
        "p-1 " +
        "disabled:cursor-not-allowed " +
        "disabled:opacity-60"
);
