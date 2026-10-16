/*
 * LaStarter i18n : configuration i18next partagee.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

import i18next from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./locales/en.json";
import fr from "./locales/fr.json";

export const DEFAULT_LOCALE = "fr";
export const SUPPORTED_LOCALES = ["fr", "en"] as const;
export type Locale = (typeof SUPPORTED_LOCALES)[number];

/** Ressources par langue. Chaque app peut ajouter ses namespaces. */
export const resources = {
    fr: { translation: fr },
    en: { translation: en },
} as const;

/** Initialiser i18next (appeler une fois au boot de l'app). */
export async function initI18n(locale: Locale = DEFAULT_LOCALE): Promise<typeof i18next> {
    if (!i18next.isInitialized) {
        await i18next.use(initReactI18next).init({
            resources,
            lng: locale,
            fallbackLng: DEFAULT_LOCALE,
            interpolation: { escapeValue: false },
            react: { useSuspense: false },
        });
    }
    return i18next;
}

/** Detecter la langue du navigateur. */
export function detectLocale(): Locale {
    const nav = typeof navigator !== "undefined" ? navigator.language : DEFAULT_LOCALE;
    const short = nav.split("-")[0]?.toLowerCase();
    return (SUPPORTED_LOCALES as readonly string[]).includes(short)
        ? (short as Locale)
        : DEFAULT_LOCALE;
}

/** Ajouter un namespace specifique a une app (lazy loading). */
export function addNamespace(
    locale: Locale,
    ns: string,
    translations: Record<string, unknown>,
): void {
    i18next.addResourceBundle(locale, ns, translations, true, true);
}
