/*
 * LaStarter UI : Typography (composants de texte avec tokens Compound).
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import React from "react";
import styles from "./Typography.module.css";

export type TypographyVariant = "h1" | "h2" | "h3" | "h4" | "body" | "bodySm" | "caption" | "label";

export interface TypographyProps {
    variant?: TypographyVariant;
    /** Couleur : primary (defaut), secondary, inverted, accent. */
    color?: "primary" | "secondary" | "inverted" | "accent";
    /** Graisse : regular, medium, semibold. */
    weight?: "regular" | "medium" | "semibold";
    /** Contenu. */
    children: React.ReactNode;
    /** Element HTML personnalise (defaut selon variant). */
    as?: keyof React.JSX.IntrinsicElements;
    className?: string;
}

const defaultTags: Record<TypographyVariant, keyof React.JSX.IntrinsicElements> = {
    h1: "h1",
    h2: "h2",
    h3: "h3",
    h4: "h4",
    body: "p",
    bodySm: "p",
    caption: "span",
    label: "span",
};

export function Typography({
    variant = "body",
    color = "primary",
    weight,
    children,
    as,
    className,
}: TypographyProps) {
    const Tag = as ?? defaultTags[variant];
    return React.createElement(
        Tag,
        {
            className:
                `${styles[variant]} ${styles[color]} ${weight ? styles[weight] : ""} ${className ?? ""}`.trim(),
        },
        children,
    );
}
