import type React from "react";
import styles from "./Badge.module.css";

export type BadgeVariant = "accent" | "danger" | "info" | "neutral" | "success" | "warning";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
    variant?: BadgeVariant;
    children: React.ReactNode;
}

export function Badge({ variant = "neutral", children, className, ...rest }: BadgeProps) {
    return (
        <span className={`${styles.badge} ${className ?? ""}`} data-variant={variant} {...rest}>
            {children}
        </span>
    );
}
