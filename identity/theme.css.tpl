/*
 * LaStarter — theme.css : design system Compound (Element) appliqué partout.
 * SOURCE OFFICIELLE : compound-design-tokens + compound-web (npm).
 * Chaque règle ci-dessous reprend les specs EXACTES des composants Compound,
 * adaptées pour re-themer les apps La Suite (Cunningham) sans les modifier.
 *
 * Jetons : {{token}} rendus par le CLI depuis themes/*.toml.
 */

/* ================================================================
 * FONTS — Inter (même source qu'Element Web : @fontsource/inter)
 * Servi par la passerelle sur /__lastarter/fonts/
 * ================================================================ */
@font-face {
    font-family: "Inter";
    font-style: normal;
    font-weight: 400;
    font-display: swap;
    src: url("/__lastarter/fonts/inter-400.woff2") format("woff2");
}
@font-face {
    font-family: "Inter";
    font-style: normal;
    font-weight: 500;
    font-display: swap;
    src: url("/__lastarter/fonts/inter-500.woff2") format("woff2");
}
@font-face {
    font-family: "Inter";
    font-style: normal;
    font-weight: 600;
    font-display: swap;
    src: url("/__lastarter/fonts/inter-600.woff2") format("woff2");
}

:root {
    /* ================================================================
     * 1. TOKENS COMPOUND — palette complète (light/dark via themes/*.toml)
     * ================================================================ */
    --cpd-color-gray-100: {{neutral_25}};
    --cpd-color-gray-200: {{neutral_50}};
    --cpd-color-gray-300: {{neutral_100}};
    --cpd-color-gray-400: {{neutral_150}};
    --cpd-color-gray-500: {{neutral_250}};
    --cpd-color-gray-600: {{neutral_300}};
    --cpd-color-gray-700: {{neutral_450}};
    --cpd-color-gray-800: {{neutral_550}};
    --cpd-color-gray-900: {{neutral_650}};
    --cpd-color-gray-1000: {{neutral_750}};
    --cpd-color-gray-1100: {{neutral_850}};
    --cpd-color-gray-1200: {{neutral_950}};
    --cpd-color-gray-1300: {{neutral_1000}};
    --cpd-color-gray-1400: {{neutral_1100}};

    --cpd-color-green-300: {{primary_300}};
    --cpd-color-green-700: {{primary_700}};
    --cpd-color-green-800: {{primary_800}};
    --cpd-color-green-900: {{primary_900}};

    --cpd-color-red-300: {{danger_300}};
    --cpd-color-red-900: {{danger_900}};

    --cpd-color-blue-1100: {{info_1100}};

    /* Sémantique Compound (mapping officiel). */
    --cpd-color-text-primary: var(--cpd-color-gray-1400);
    --cpd-color-text-secondary: var(--cpd-color-gray-900);
    --cpd-color-text-disabled: var(--cpd-color-gray-800);
    --cpd-color-text-action-accent: var(--cpd-color-green-900);
    --cpd-color-text-link-external: var(--cpd-color-blue-1100);
    --cpd-color-text-critical-primary: var(--cpd-color-red-900);
    --cpd-color-text-on-solid-primary: {{neutral_0}};
    --cpd-color-bg-canvas-default: {{canvas}};
    --cpd-color-bg-subtle-primary: var(--cpd-color-gray-400);
    --cpd-color-bg-subtle-secondary: var(--cpd-color-gray-300);
    --cpd-color-bg-action-primary-rest: var(--cpd-color-gray-1400);
    --cpd-color-bg-action-primary-hovered: var(--cpd-color-gray-1200);
    --cpd-color-bg-action-primary-pressed: var(--cpd-color-gray-1100);
    --cpd-color-bg-action-primary-disabled: var(--cpd-color-gray-700);
    --cpd-color-bg-accent-rest: var(--cpd-color-green-900);
    --cpd-color-bg-accent-hovered: var(--cpd-color-green-800);
    --cpd-color-bg-accent-subtle: var(--cpd-color-green-300);
    --cpd-color-bg-critical-subtle: var(--cpd-color-red-300);
    --cpd-color-border-interactive-primary: var(--cpd-color-gray-600);
    --cpd-color-border-interactive-secondary: var(--cpd-color-gray-400);
    --cpd-color-border-interactive-hovered: var(--cpd-color-gray-800);
    --cpd-color-separator-primary: var(--cpd-color-gray-400);

    /* Géométrie Compound. */
    --cpd-radius-pill-effect: 9999px;
    --cpd-radius-small: 4px;
    --cpd-radius-medium: 8px;
    --cpd-space-1x: 4px;
    --cpd-space-2x: 8px;
    --cpd-space-3x: 12px;
    --cpd-space-4x: 16px;
    --cpd-space-5x: 20px;
    --cpd-space-9x: 36px;
    --cpd-font-family-sans: {{font_family}};

    /* ================================================================
     * 2. PONT CUNNINGHAM → palette Compound (toute l'échelle)
     * ================================================================ */
    --c--globals--colors--brand-050: {{primary_50}};
    --c--globals--colors--brand-100: {{primary_100}};
    --c--globals--colors--brand-150: {{primary_150}};
    --c--globals--colors--brand-200: {{primary_200}};
    --c--globals--colors--brand-250: {{primary_250}};
    --c--globals--colors--brand-300: {{primary_300}};
    --c--globals--colors--brand-350: {{primary_350}};
    --c--globals--colors--brand-400: {{primary_400}};
    --c--globals--colors--brand-450: {{primary_450}};
    --c--globals--colors--brand-500: {{primary_500}};
    --c--globals--colors--brand-550: {{primary_550}};
    --c--globals--colors--brand-600: {{primary_600}};
    --c--globals--colors--brand-650: {{primary_650}};
    --c--globals--colors--brand-700: {{primary_700}};
    --c--globals--colors--brand-750: {{primary_750}};
    --c--globals--colors--brand-800: {{primary_800}};
    --c--globals--colors--brand-850: {{primary_850}};
    --c--globals--colors--brand-900: {{primary_900}};
    --c--globals--colors--brand-950: {{primary_950}};
    --c--globals--colors--logo-1-light: {{primary_700}};
    --c--globals--colors--logo-2-light: {{primary_700}};
    --c--globals--colors--logo-1-dark: {{primary_700}};
    --c--globals--colors--logo-2-dark: {{primary_700}};

    --c--globals--colors--gray-000: {{neutral_0}};
    --c--globals--colors--gray-025: {{neutral_25}};
    --c--globals--colors--gray-050: {{neutral_50}};
    --c--globals--colors--gray-100: {{neutral_100}};
    --c--globals--colors--gray-150: {{neutral_150}};
    --c--globals--colors--gray-200: {{neutral_200}};
    --c--globals--colors--gray-250: {{neutral_250}};
    --c--globals--colors--gray-300: {{neutral_300}};
    --c--globals--colors--gray-350: {{neutral_350}};
    --c--globals--colors--gray-400: {{neutral_400}};
    --c--globals--colors--gray-450: {{neutral_450}};
    --c--globals--colors--gray-500: {{neutral_500}};
    --c--globals--colors--gray-550: {{neutral_550}};
    --c--globals--colors--gray-600: {{neutral_600}};
    --c--globals--colors--gray-650: {{neutral_650}};
    --c--globals--colors--gray-700: {{neutral_700}};
    --c--globals--colors--gray-750: {{neutral_750}};
    --c--globals--colors--gray-800: {{neutral_800}};
    --c--globals--colors--gray-850: {{neutral_850}};
    --c--globals--colors--gray-900: {{neutral_900}};
    --c--globals--colors--gray-950: {{neutral_950}};
    --c--globals--colors--gray-1000: {{neutral_1100}};

    --c--globals--colors--info-050: {{info_100}};
    --c--globals--colors--info-100: {{info_100}};
    --c--globals--colors--info-500: {{info_500}};
    --c--globals--colors--info-550: {{info_900}};
    --c--globals--colors--info-900: {{info_1100}};
    --c--globals--colors--success-050: {{success_100}};
    --c--globals--colors--success-100: {{success_100}};
    --c--globals--colors--success-500: {{success_500}};
    --c--globals--colors--success-550: {{success_900}};
    --c--globals--colors--success-900: {{success_1100}};
    --c--globals--colors--warning-050: {{warning_100}};
    --c--globals--colors--warning-100: {{warning_100}};
    --c--globals--colors--warning-500: {{warning_500}};
    --c--globals--colors--warning-550: {{warning_900}};
    --c--globals--colors--warning-900: {{warning_1100}};
    --c--globals--colors--error-050: {{danger_100}};
    --c--globals--colors--error-100: {{danger_100}};
    --c--globals--colors--error-500: {{danger_500}};
    --c--globals--colors--error-550: {{danger_900}};
    --c--globals--colors--error-900: {{danger_1100}};

    --c--globals--font--families--base: {{font_family}};
    --c--globals--font--families--accent: {{font_family}};

    --c--components--button--border-radius: var(--cpd-radius-pill-effect);
    --c--components--button--border-radius--active: var(--cpd-radius-pill-effect);
    --c--components--button--border-radius--focus: var(--cpd-radius-pill-effect);
    --c--components--button--medium-height: 36px;

    /* Fonds de section « brand » → NEUTRES (pas d'aplat vert). */
    --c--contextuals--background--semantic--brand--primary: var(--c--globals--colors--gray-1000);
    --c--contextuals--background--semantic--brand--primary-hover: var(--c--globals--colors--gray-950);
    --c--contextuals--background--semantic--brand--secondary: var(--c--globals--colors--gray-100);
    --c--contextuals--background--semantic--brand--secondary-hover: var(--c--globals--colors--gray-150);
    --c--contextuals--background--semantic--brand--tertiary: var(--c--globals--colors--gray-50);
    --c--contextuals--background--semantic--brand--tertiary-hover: var(--c--globals--colors--gray-100);
    --c--contextuals--content--semantic--brand--on-brand: #ffffff;

    /* ================================================================
     * 3. MARQUE BLANCHE
     * ================================================================ */
    --lastarter-brand-name: "{{brand_name}}";
    --lastarter-brand-color: {{brand_color}};
    --lastarter-logo-url: url("{{logo_url}}");
    --lastarter-canvas: {{canvas}};
}

/* ----------------------------------------------------------------
 * JETONS UNIQUEMENT — aucune règle structurelle.
 * Les apps La Suite (docs/drive/meet) tournent sur Cunningham : elles
 * consomment nativement les jetons --c--* ci-dessus (couleurs, rayons,
 * polices, boutons). Rethemer = réassigner les jetons, pas réécrire les
 * composants : chaque app garde sa géométrie native, sans cumul de
 * styles (le bug « boutons doublés »). Discussions (Element) reste en
 * Compound natif (thème non injecté) ; le portail et le thème Keycloak
 * ont leurs propres feuilles (portal.css, identity/keycloak-theme)
 * bâties sur les mêmes jetons vendus dans libs/compound/.
 * ---------------------------------------------------------------- */

/* ================================================================
 * MEET — remap des classes atomiques (classgen compilée en dur).
 * Le build meet fige ses couleurs dans des classes utilitaires
 * (bg-c_primary.800 = bleu DSFR littéral) : le pont de jetons ne les
 * atteint pas. Substitution 1:1 — couleur pour couleur, rayon pour
 * rayon — vers les jetons Compound ci-dessus. Si l'amont renomme ses
 * classes, ces règles cessent simplement de matcher (dégradation
 * gracieuse vers le natif). AUCUNE règle géométrique ici.
 * ================================================================ */
.bg-c_primary\.800 { background-color: var(--cpd-color-bg-action-primary-rest) !important; }
.bg-c_primary\.800:is([data-hovered]) { background-color: var(--cpd-color-bg-action-primary-hovered) !important; }
.bg-c_primary\.800:is([data-pressed]) { background-color: var(--cpd-color-bg-action-primary-pressed) !important; }
.bg-c_primary\.300 { background-color: var(--cpd-color-bg-accent-subtle) !important; }
.c_primary\.800 { color: var(--cpd-color-text-action-accent) !important; }
.bd-c_primary\.800 { border-color: var(--cpd-color-bg-accent-rest) !important; }
.bdr_4 { border-radius: var(--cpd-radius-pill-effect) !important; }
