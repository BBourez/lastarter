/*
 * LaStarter — refonte UI complète au style Element (Compound).
 * Design system officiel : compound.element.io (@vector-im/compound-*).
 *
 * Structure :
 *   1. TOKENS COMPOUND : la palette (light/dark) est rendue depuis themes/*.toml
 *      → les composants ci-dessous référencent var(--cpd-*) et s'adaptent.
 *   2. PONT CUNNINGHAM : les apps La Suite (Cunningham) héritent de la palette.
 *   3. COMPOSANTS : restylage boutons, formulaires, sidebars, cartes, etc.
 *      au look exact d'Element Web / Element Call.
 *
 * Jetons restants : {{brand_name}}, {{brand_color}} (seuls éléments dynamiques
 * hors palette — la palette vient de themes/*.toml via le CLI).
 */

:root {
    /* ================================================================
     * 1. TOKENS COMPOUND — palette rendue par le CLI (light ou dark)
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

    /* Sémantique — mapping officiel Compound. */
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
     * 2. PONT CUNNINGHAM → palette Compound
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

    /* ================================================================
     * 3. MARQUE BLANCHE
     * ================================================================ */
    --lastarter-brand-name: "{{brand_name}}";
    --lastarter-brand-color: {{brand_color}};
    --lastarter-logo-url: url("{{logo_url}}");
    --lastarter-canvas: {{canvas}};
}

/* ================================================================
 * COMPOSANTS — restylage complet au style Element
 * Les sélecteurs !important sont requis : ce CSS charge APRÈS les apps.
 * ================================================================ */

/* ---------- Base : police et couleurs ---------- */
body, html {
    font-family: var(--cpd-font-family-sans) !important;
    color: var(--cpd-color-text-primary);
    background-color: var(--cpd-color-bg-canvas-default);
}

h1, h2, h3, h4, h5, h6 {
    font-family: var(--cpd-font-family-sans) !important;
    color: var(--cpd-color-text-primary);
    font-weight: 600 !important;
    letter-spacing: -0.01em;
}

h1 { font-size: 1.5rem !important; }
h2 { font-size: 1.25rem !important; }
h3 { font-size: 1.125rem !important; }

/* ---------- BOUTONS : pilule, comme Element ---------- */
button,
input[type="submit"],
input[type="button"] {
    border-radius: var(--cpd-radius-pill-effect) !important;
    font-family: var(--cpd-font-family-sans) !important;
    font-weight: 500 !important;
    font-size: 0.9375rem !important;
    min-height: 36px;
    padding: 6px 20px;
    transition: background-color 0.1s, border-color 0.1s, color 0.1s;
    cursor: pointer;
    letter-spacing: 0;
    line-height: 1.25;
}

/* Primary : gris très foncé plein (Element n'utilise pas le vert ici). */
button[type="submit"],
[class*="--primary"]:not([class*="--primary-outline"]):not([class*="text-primary"]),
[class*="btn-primary"]:not([class*="outline"]):not([class*="ghost"]),
[class*="is-primary"],
[class*="variant-primary"],
[class*="kind-primary"],
[data-kind="primary"] {
    background-color: var(--cpd-color-bg-action-primary-rest) !important;
    color: var(--cpd-color-text-on-solid-primary) !important;
    border: none !important;
}

button[type="submit"]:hover,
[class*="--primary"]:not([class*="outline"]):hover,
[class*="btn-primary"]:not([class*="outline"]):hover,
[class*="is-primary"]:hover,
[data-kind="primary"]:hover {
    background-color: var(--cpd-color-bg-action-primary-hovered) !important;
}

button[type="submit"]:active,
[data-kind="primary"]:active {
    background-color: var(--cpd-color-bg-action-primary-pressed) !important;
}

/* Secondary : blanc, bordure grise. */
[class*="--secondary"],
[class*="btn-secondary"],
[class*="variant-secondary"],
[class*="outline"],
[data-kind="secondary"] {
    background-color: var(--cpd-color-bg-canvas-default) !important;
    color: var(--cpd-color-text-primary) !important;
    border: 1px solid var(--cpd-color-border-interactive-secondary) !important;
}

[class*="--secondary"]:hover,
[data-kind="secondary"]:hover {
    border-color: var(--cpd-color-border-interactive-hovered) !important;
    background-color: var(--cpd-color-bg-subtle-secondary) !important;
}

/* Tertiary : souligné, transparent. */
[class*="--tertiary"],
[class*="ghost"],
[class*="variant-ghost"],
[data-kind="tertiary"] {
    background-color: transparent !important;
    color: var(--cpd-color-text-primary) !important;
    border: none !important;
    text-decoration: underline;
}

/* Danger. */
[class*="destructive"],
[class*="btn-danger"],
[class*="variant-danger"] {
    background-color: var(--cpd-color-red-900) !important;
    color: #fff !important;
    border: none !important;
}

/* Désactivé. */
button:disabled,
[aria-disabled="true"] {
    background-color: var(--cpd-color-bg-action-primary-disabled) !important;
    color: var(--cpd-color-text-on-solid-primary) !important;
    cursor: not-allowed !important;
}

/* ---------- FORMULAIRES : champs Element ---------- */
input[type="text"], input[type="password"], input[type="email"],
input[type="number"], input[type="search"], input[type="url"],
input[type="tel"], input[type="date"],
textarea, select {
    font-family: var(--cpd-font-family-sans) !important;
    font-size: 0.9375rem !important;
    color: var(--cpd-color-text-primary) !important;
    background-color: var(--cpd-color-bg-canvas-default) !important;
    border: 1px solid var(--cpd-color-border-interactive-primary) !important;
    border-radius: var(--cpd-radius-medium) !important;
    padding: 8px 12px;
    min-height: 36px;
    transition: border-color 0.1s, box-shadow 0.1s;
}

input:focus, textarea:focus, select:focus {
    outline: none !important;
    border-color: var(--cpd-color-text-action-accent) !important;
    box-shadow: 0 0 0 2px var(--cpd-color-bg-accent-subtle) !important;
}

input::placeholder, textarea::placeholder {
    color: var(--cpd-color-text-secondary) !important;
}

label {
    font-weight: 500 !important;
    color: var(--cpd-color-text-primary);
    font-size: 0.875rem;
}

/* ---------- LIENS : vert Element ---------- */
a:not([class*="btn"]):not([class*="button"]):not([class*="tile"]):not([class*="tab"]) {
    color: var(--cpd-color-text-action-accent);
    text-decoration: none;
}

a:not([class*="btn"]):hover {
    color: var(--cpd-color-bg-accent-hovered);
}

/* ---------- CARTES / PANNEAUX ---------- */
[class*="card"],
[class*="modal-content"],
[class*="dialog"]:not([class*="dialog-overlay"]) {
    border-radius: var(--cpd-radius-medium) !important;
    border: 1px solid var(--cpd-color-border-interactive-secondary);
    box-shadow: 0 1px 2px rgba(0,0,0,0.06) !important;
}

/* ---------- SIDEBAR / NAVIGATION — style Element Web ---------- */
aside,
nav[class*="sidebar"],
[class*="Sidebar"]:not([class*="item"]):not([class*="content"]) {
    background-color: var(--cpd-color-bg-subtle-secondary) !important;
}

[class*="sidebar"] a,
[class*="sidebar"] button,
[class*="nav-item"],
[class*="menu-item"] {
    border-radius: var(--cpd-radius-medium) !important;
}

[class*="sidebar"] a:hover,
[class*="nav-item"]:hover,
[class*="menu-item"]:hover {
    background-color: var(--cpd-color-bg-subtle-primary) !important;
}

[class*="active"],
[aria-current="page"] {
    background-color: var(--cpd-color-bg-accent-subtle) !important;
    color: var(--cpd-color-text-action-accent) !important;
}

/* ---------- TABLES ---------- */
th {
    font-weight: 500 !important;
    color: var(--cpd-color-text-secondary) !important;
    font-size: 0.8125rem !important;
}

td {
    border-bottom: 1px solid var(--cpd-color-bg-subtle-primary);
}

/* ---------- BADGES : pilule ---------- */
[class*="badge"], [class*="tag"], [class*="chip"] {
    border-radius: var(--cpd-radius-pill-effect) !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    padding: 2px 10px !important;
}

/* ---------- CHECKBOX / RADIO ---------- */
input[type="checkbox"], input[type="radio"] {
    accent-color: var(--cpd-color-green-700) !important;
}

/* ---------- SCROLLBARS fines ---------- */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background-color: var(--cpd-color-gray-500);
    border-radius: var(--cpd-radius-pill-effect);
}

/* ---------- FOCUS VISIBLE ---------- */
button:focus-visible, a:focus-visible,
input:focus-visible, select:focus-visible, textarea:focus-visible {
    outline: 2px solid var(--cpd-color-green-700) !important;
    outline-offset: 2px;
}

/* ================================================================
 * CLASSES CUNNINGHAM EXACTES — extraites des CSS de production
 * (drive, messages, transfers : c__button--brand--*, c__dropdown-menu…)
 * Ces sélecteurs précisent les patterns génériques ci-dessus.
 * ================================================================ */

/* Boutons Cunningham : pilule Element */
.c__button,
button.c__button {
    border-radius: var(--cpd-radius-pill-effect) !important;
    font-family: var(--cpd-font-family-sans) !important;
    font-weight: 500 !important;
    min-height: 36px;
}

/* Primary : gris foncé plein */
.c__button--brand--primary,
.c__button--error--primary {
    background-color: var(--cpd-color-bg-action-primary-rest) !important;
    color: var(--cpd-color-text-on-solid-primary) !important;
    border: none !important;
}

.c__button--brand--primary:hover,
.c__button--error--primary:hover {
    background-color: var(--cpd-color-bg-action-primary-hovered) !important;
}

/* Secondary : blanc bordé */
.c__button--brand--secondary,
.c__button--error--secondary {
    background-color: var(--cpd-color-bg-canvas-default) !important;
    color: var(--cpd-color-text-primary) !important;
    border: 1px solid var(--cpd-color-border-interactive-secondary) !important;
}

.c__button--brand--secondary:hover {
    border-color: var(--cpd-color-border-interactive-hovered) !important;
    background-color: var(--cpd-color-bg-subtle-secondary) !important;
}

/* Tertiary : souligné */
.c__button--brand--tertiary,
.c__button--error--tertiary {
    background-color: transparent !important;
    color: var(--cpd-color-text-primary) !important;
    border: none !important;
}

/* Bordered (variante outline Cunningham) */
.c__button--brand--bordered,
.c__button--error--bordered {
    background-color: transparent !important;
    border: 1px solid var(--cpd-color-border-interactive-primary) !important;
    color: var(--cpd-color-text-primary) !important;
}

/* Dropdowns Cunningham */
.c__dropdown-menu,
[class*="dropdown-menu"] {
    border-radius: var(--cpd-radius-medium) !important;
    border: 1px solid var(--cpd-color-border-interactive-secondary) !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12) !important;
}

/* Items de menu Cunningham */
.c__dropdown-menu [role="menuitem"],
.c__dropdown-menu li,
[class*="menu--item"],
[class*="menu__item"] {
    border-radius: var(--cpd-radius-small) !important;
}

/* Alertes Cunningham */
.c__alert {
    border-radius: var(--cpd-radius-medium) !important;
}

/* Inputs Cunningham (si classes spécifiques) */
.c__input,
[class*="c__text-field"],
[class*="c__input"] {
    border-radius: var(--cpd-radius-medium) !important;
    font-family: var(--cpd-font-family-sans) !important;
}

/* ================================================================
 * PROJECTS (React CRA) — classes CSS modules observées
 * ================================================================ */

/* Sidebar gauche : LeftMenu_* */
[class*="LeftMenu_boards"],
[class*="LeftMenu_projects"] {
    font-family: var(--cpd-font-family-sans) !important;
}

[class*="LeftMenu_addBoardButton"],
[class*="Board_addCardButton"],
[class*="Board_listHeaderButton"],
[class*="CardModal_optionsButton"] {
    border-radius: var(--cpd-radius-pill-effect) !important;
}

/* Fond des menus déroulants Projects */
[class*="Core_menuBackdrop"] {
    background: rgba(0, 0, 0, 0.3) !important;
}
