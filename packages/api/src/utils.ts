/*
 * LaStarter API : utilitaires formateurs.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

/** Formater une taille de fichier. */
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
