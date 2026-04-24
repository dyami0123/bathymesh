import type { ComponentProps } from "react";
import type { VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { heading as headingStyles } from "./styles";

type HeadingProps = ComponentProps<"h2"> &
    VariantProps<typeof headingStyles> & {
        as?: "h1" | "h2" | "h3" | "h4";
    };

export function Heading({
    level,
    as: Tag = "h2",
    className,
    children,
    ...rest
}: HeadingProps) {
    return (
        <Tag className={cn(headingStyles({ level }), className)} {...rest}>
            {children}
        </Tag>
    );
}
