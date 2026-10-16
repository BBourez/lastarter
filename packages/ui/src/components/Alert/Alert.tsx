import type React from "react";
import styles from "./Alert.module.css";

export type AlertVariant = "success" | "error" | "warning" | "info";
export interface AlertProps {
    variant: AlertVariant;
    children: React.ReactNode;
}

export function Alert({ variant, children }: AlertProps) {
    return (
        <div className={styles.alert} data-variant={variant} role="alert">
            <div className={styles.content}>{children}</div>
        </div>
    );
}
