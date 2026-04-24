import type { ComponentProps } from "react";
import type { VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { badge as badgeStyles } from "./styles";

type BadgeProps = ComponentProps<"div"> &
    VariantProps<typeof badgeStyles> & {
        as?: "div" | "p" | "span";
        role?: string;
    };

export function Badge({
    intent,
    as: Tag = "div",
    className,
    children,
    ...rest
}: BadgeProps) {
    return (
        <Tag className={cn(badgeStyles({ intent }), className)} {...rest}>
            {children}
        </Tag>
    );
}
