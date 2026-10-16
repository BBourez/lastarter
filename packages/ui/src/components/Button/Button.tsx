/*
 * LaStarter UI — Button (copie conforme Compound Web Button).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: AGPL-3.0-only.
 */

import React, { forwardRef } from "react";
import classNames from "classnames";
import styles from "./Button.module.css";

export type ButtonKind = "primary" | "accent" | "secondary" | "tertiary" | "destructive";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    /** Variant visuel (défaut: primary = gris foncé comme Element) */
    kind?: ButtonKind;
    /** Taille (défaut: md = 36px) */
    size?: ButtonSize;
    /** Rendu en <a> avec href */
    href?: string;
    children: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ kind = "primary", size = "md", href, className, children, ...rest }, ref) => {
        const cls = classNames(styles.button, className);
        const dataProps = {
            "data-kind": kind,
            "data-size": size,
        };

        if (href) {
            return (
                <a ref={ref as never} href={href} className={cls} {...dataProps} {...(rest as never)}>
                    {children}
                </a>
            );
        }

        return (
            <button ref={ref} type="button" className={cls} {...dataProps} {...rest}>
                {children}
            </button>
        );
    }
);

Button.displayName = "Button";
