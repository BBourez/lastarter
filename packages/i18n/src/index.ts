/*
 * LaStarter i18n : exports publics.
 * Copyright 2026 LaStarter. SPDX-License-Identifier: Proprietary.
 */

export {
    initI18n,
    detectLocale,
    addNamespace,
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
    resources,
} from "./config";
export type { Locale } from "./config";

/* Re-export react-i18next pour convenance (useTranslation, Trans, etc.) */
export { useTranslation, Trans, I18nextProvider } from "react-i18next";
