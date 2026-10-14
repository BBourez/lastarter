/*
 * LaStarter — theme.css (rendu par lastarter-cli, jamais édité à la main).
 * Sert sur /__lastarter/theme.css sur TOUS les sous-domaines via la passerelle.
 *
 * Double rôle :
 *   1. PONT CUNNINGHAM → COMPOUND : les apps La Suite (Drive, Messages,
 *      Transfers, Projects) lisent des tokens `--c--*` (design system
 *      Cunningham). Leurs tokens sémantiques référencent la palette de base
 *      via var() : redéfinir la palette re-theme toute l'app, sans toucher
 *      aux images amont.
 *   2. MARQUE BLANCHE : variables `--lastarter-*` (nom, logo, couleur) lues
 *      par le portail et le thème Keycloak.
 *
 * Jetons : {{KEY}} (substitués par le CLI depuis themes/*.toml + les
 * réponses d'installation).
 */

:root {
    /* ================================================================
     * 1. PONT CUNNINGHAM → PALETTE COMPOUND
     * ================================================================ */

    /* Échelle « brand » (violet La Suite) → primaire du thème (vert Element). */
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

    /* Logo des apps La Suite → primaire du thème. */
    --c--globals--colors--logo-1-light: {{primary_700}};
    --c--globals--colors--logo-2-light: {{primary_700}};
    --c--globals--colors--logo-1-dark: {{primary_700}};
    --c--globals--colors--logo-2-dark: {{primary_700}};

    /* Échelle « gray » (neutre). */
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
    --c--globals--colors--gray-1000: {{neutral_1050}};

    /* Statuts sémantiques. */
    --c--globals--colors--info-050: {{info_100}};
    --c--globals--colors--info-100: {{info_100}};
    --c--globals--colors--info-150: {{info_300}};
    --c--globals--colors--info-200: {{info_300}};
    --c--globals--colors--info-250: {{info_500}};
    --c--globals--colors--info-300: {{info_500}};
    --c--globals--colors--info-350: {{info_700}};
    --c--globals--colors--info-400: {{info_700}};
    --c--globals--colors--info-450: {{info_900}};
    --c--globals--colors--info-500: {{info_900}};
    --c--globals--colors--info-550: {{info_1100}};
    --c--globals--colors--info-600: {{info_1100}};
    --c--globals--colors--info-650: {{info_1400}};
    --c--globals--colors--info-700: {{info_1400}};

    --c--globals--colors--success-050: {{success_100}};
    --c--globals--colors--success-100: {{success_100}};
    --c--globals--colors--success-150: {{success_300}};
    --c--globals--colors--success-200: {{success_300}};
    --c--globals--colors--success-250: {{success_500}};
    --c--globals--colors--success-300: {{success_500}};
    --c--globals--colors--success-350: {{success_700}};
    --c--globals--colors--success-400: {{success_700}};
    --c--globals--colors--success-450: {{success_900}};
    --c--globals--colors--success-500: {{success_900}};
    --c--globals--colors--success-550: {{success_1100}};
    --c--globals--colors--success-600: {{success_1100}};
    --c--globals--colors--success-650: {{success_1400}};
    --c--globals--colors--success-700: {{success_1400}};

    --c--globals--colors--warning-050: {{warning_100}};
    --c--globals--colors--warning-100: {{warning_100}};
    --c--globals--colors--warning-150: {{warning_300}};
    --c--globals--colors--warning-200: {{warning_300}};
    --c--globals--colors--warning-250: {{warning_500}};
    --c--globals--colors--warning-300: {{warning_500}};
    --c--globals--colors--warning-350: {{warning_700}};
    --c--globals--colors--warning-400: {{warning_700}};
    --c--globals--colors--warning-450: {{warning_900}};
    --c--globals--colors--warning-500: {{warning_900}};
    --c--globals--colors--warning-550: {{warning_1100}};
    --c--globals--colors--warning-600: {{warning_1100}};
    --c--globals--colors--warning-650: {{warning_1400}};
    --c--globals--colors--warning-700: {{warning_1400}};

    --c--globals--colors--error-050: {{danger_100}};
    --c--globals--colors--error-100: {{danger_100}};
    --c--globals--colors--error-150: {{danger_300}};
    --c--globals--colors--error-200: {{danger_300}};
    --c--globals--colors--error-250: {{danger_500}};
    --c--globals--colors--error-300: {{danger_500}};
    --c--globals--colors--error-350: {{danger_700}};
    --c--globals--colors--error-400: {{danger_700}};
    --c--globals--colors--error-450: {{danger_900}};
    --c--globals--colors--error-500: {{danger_900}};
    --c--globals--colors--error-550: {{danger_1100}};
    --c--globals--colors--error-600: {{danger_1100}};
    --c--globals--colors--error-650: {{danger_1400}};
    --c--globals--colors--error-700: {{danger_1400}};

    /* Palette « red » libre de Cunningham → danger. */
    --c--globals--colors--red-500: {{danger_900}};

    /* Typographie → Inter (police Compound). */
    --c--globals--font--families--base: {{font_family}};
    --c--globals--font--families--accent: {{font_family}};

    /* Composants — géométrie alignée sur Compound. */
    --c--components--button--border-radius: {{button_radius}};
    --c--components--button--border-radius--active: {{button_radius}};
    --c--components--button--border-radius--focus: {{button_radius}};
    --c--components--button--medium-height: {{button_height}};

    /* ================================================================
     * 2. MARQUE BLANCHE — lues par le portail et le thème Keycloak.
     * ================================================================ */
    --lastarter-brand-name: "{{brand_name}}";
    --lastarter-brand-color: {{brand_color}};
    --lastarter-logo-url: url("{{logo_url}}");
    --lastarter-canvas: {{canvas}};
}

/* Fond de page global pour les apps La Suite (optionnel : léger tint). */
/* body { background-color: {{canvas}}; } */
