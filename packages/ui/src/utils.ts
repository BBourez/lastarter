/*
 * LaStarter UI : utilitaires partages.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import classNames from "classnames";

/** Alias pour classnames (meme API que Element Web). */
export const cn = classNames;

/** Initiales a partir d'un nom complet (max 2). */
export function getInitials(name: string): string {
    return name
        .split(" ")
        .map((word) => word[0])
        .filter(Boolean)
        .slice(0, 2)
        .join("")
        .toUpperCase();
}

/** Formater une taille de fichier en octets lisibles. */
export function formatFileSize(bytes: number, locale = "fr"): string {
    const units = locale === "fr" ? ["o", "Ko", "Mo", "Go"] : ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${Math.round(size * 10) / 10} ${units[unitIndex]}`;
}

/** Debounce pour les inputs de recherche. */
export function debounce<T extends (...args: never[]) => void>(fn: T, delayMs: number): T {
    let timer: ReturnType<typeof setTimeout> | undefined;
    return ((...args: Parameters<T>) => {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delayMs);
    }) as T;
}

/** Verifier si une valeur est definie (non-null, non-undefined). */
export function isDefined<T>(value: T | null | undefined): value is T {
    return value !== null && value !== undefined;
}
