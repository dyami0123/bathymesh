import type { ComponentProps } from "react";
import type { VariantProps } from "class-variance-authority";
import { cn } from "@/lib/cn";
import { card as cardStyles } from "./styles";

type CardProps = ComponentProps<"div"> &
    VariantProps<typeof cardStyles> & {
        as?: "div" | "section";
    };

export function Card({
    variant,
    as: Tag = "div",
    className,
    children,
    ...rest
}: CardProps) {
    return (
        <Tag className={cn(cardStyles({ variant }), className)} {...rest}>
            {children}
        </Tag>
    );
}
