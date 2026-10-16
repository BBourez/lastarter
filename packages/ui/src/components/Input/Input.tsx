/*
 * LaStarter UI : Input (copie conforme Compound Form).
 * Copyright 2026 LaStarter. Base sur Compound (Element).
 */

import React, { forwardRef } from "react";
import styles from "./Input.module.css";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    /** Label affiche au-dessus. */
    label?: string;
    /** Message d'erreur (rend aria-invalid). */
    error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(function Input(
    { label, error, className, ...rest },
    ref,
) {
    return (
        <label style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
            {label && (
                <span style={{ fontSize: "13px", fontWeight: 500, color: "var(--ls-color-text)" }}>{label}</span>
            )}
            <input
                ref={ref}
                className={`${styles.input} ${className ?? ""}`}
                aria-invalid={error ? "true" : undefined}
                {...rest}
            />
            {error && <span style={{ fontSize: "12px", color: "var(--ls-color-danger)" }}>{error}</span>}
        </label>
    );
});