import type { ComponentProps } from "react";
import type { VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { input as inputStyles } from "./styles";

type InputProps = ComponentProps<"input"> & VariantProps<typeof inputStyles>;

export function Input({ variant, width, className, ...rest }: InputProps) {
    return (
        <input
            className={cn(inputStyles({ variant, width }), className)}
            {...rest}
        />
    );
}
