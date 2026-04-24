import type { ComponentProps } from "react";
import type { VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { button as buttonStyles } from "./styles";

type ButtonProps = ComponentProps<"button"> & VariantProps<typeof buttonStyles>;

export function Button({
    intent,
    shape,
    className,
    children,
    ...rest
}: ButtonProps) {
    return (
        <button
            type="button"
            className={cn(buttonStyles({ intent, shape }), className)}
            {...rest}
        >
            {children}
        </button>
    );
}
