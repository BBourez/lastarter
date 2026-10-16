import React from "react";
import styles from "./Switch.module.css";

export interface SwitchProps {
    checked: boolean;
    onChange: (checked: boolean) => void;
    label?: string;
    disabled?: boolean;
}

export function Switch({ checked, onChange, label, disabled }: SwitchProps) {
    return (
        <label
            className={styles.wrapper}
            style={{ opacity: disabled ? 0.5 : 1, pointerEvents: disabled ? "none" : "auto" }}
        >
            <button
                type="button"
                className={styles.track}
                data-checked={checked}
                onClick={() => onChange(!checked)}
                role="switch"
                aria-checked={checked}
                aria-label={label}
            >
                <span className={styles.thumb} />
            </button>
            {label && <span className={styles.label}>{label}</span>}
        </label>
    );
}
