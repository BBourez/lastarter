/*
 * LaStarter — theme.css : design system Compound (Element) appliqué partout.
 * SOURCE OFFICIELLE : compound-design-tokens + compound-web (npm).
 * Chaque règle ci-dessous reprend les specs EXACTES des composants Compound,
 * adaptées pour re-themer les apps La Suite (Cunningham) sans les modifier.
 *
 * Jetons : {{token}} rendus par le CLI depuis themes/*.toml.
 */

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

/* ================================================================
 * TYPOGRAPHIE (Compound Typography — tailles exactes Element Call)
 * body 15px, heading 20/24/28/32, weights 400/500/600, tracking négatif
 * ================================================================ */
body, html {
    font-family: var(--cpd-font-family-sans) !important;
    font-size: 15px;
    line-height: 1.5;
    color: var(--cpd-color-text-primary);
    background-color: var(--cpd-color-bg-canvas-default);
}

h1 { font-size: 32px !important; font-weight: 600 !important; letter-spacing: -0.045em; line-height: 1.2 !important; }
h2 { font-size: 24px !important; font-weight: 600 !important; letter-spacing: -0.039em; line-height: 1.2 !important; }
h3 { font-size: 20px !important; font-weight: 600 !important; letter-spacing: -0.033em; line-height: 1.2 !important; }
h4, h5, h6 { font-size: 15px !important; font-weight: 600 !important; line-height: 1.25 !important; }

p { margin-top: 0; line-height: 1.5; }

hr {
    border: none;
    border-top: 1px solid var(--cpd-color-separator-primary);
    width: calc(100% - 24px);
    margin: 0 12px;
}

/* ================================================================
 * BUTTON (Compound Button — specs exactes)
 * radius 9999px, md=36px, primary gris foncé, secondary blanc bordé
 * ================================================================ */
button,
input[type="submit"],
input[type="button"] {
    border-radius: var(--cpd-radius-pill-effect) !important;
    font-family: var(--cpd-font-family-sans) !important;
    font-weight: 600 !important;
    font-size: 15px !important;
    min-height: var(--cpd-space-9x);
    padding: 4px 20px;
    cursor: pointer;
    letter-spacing: -0.013em;
    transition: background-color 0.1s, border-color 0.1s, color 0.1s;
    box-shadow: none !important;
}

/* Primary (Compound data-kind=primary) */
button[type="submit"],
.c__button--brand--primary,
.c__button--error--primary,
[class*="btn-primary"]:not([class*="outline"]):not([class*="ghost"]),
[class*="is-primary"],
[data-kind="primary"] {
    background: var(--cpd-color-bg-action-primary-rest) !important;
    color: var(--cpd-color-text-on-solid-primary) !important;
    border: none !important;
}

button[type="submit"]:hover, .c__button--brand--primary:hover, [data-kind="primary"]:hover {
    background: var(--cpd-color-bg-action-primary-hovered) !important;
}
button[type="submit"]:active, [data-kind="primary"]:active {
    background: var(--cpd-color-bg-action-primary-pressed) !important;
}

/* Secondary (Compound data-kind=secondary) */
.c__button--brand--secondary,
.c__button--error--secondary,
[class*="btn-secondary"],
[class*="--secondary"]:not([class*="text-secondary"]),
[data-kind="secondary"] {
    background: var(--cpd-color-bg-canvas-default) !important;
    color: var(--cpd-color-text-primary) !important;
    border: 1px solid var(--cpd-color-border-interactive-secondary) !important;
}
.c__button--brand--secondary:hover, [data-kind="secondary"]:hover {
    border-color: var(--cpd-color-border-interactive-hovered) !important;
    background: var(--cpd-color-bg-subtle-secondary) !important;
}

/* Tertiary (Compound data-kind=tertiary) */
.c__button--brand--tertiary,
.c__button--error--tertiary,
[class*="ghost"],
[data-kind="tertiary"] {
    background: transparent !important;
    color: var(--cpd-color-text-primary) !important;
    border: none !important;
    text-decoration: underline;
}

/* Destructive */
[class*="destructive"], [class*="btn-danger"] {
    background: var(--cpd-color-red-900) !important;
    color: #fff !important;
    border: none !important;
}

/* Disabled */
button:disabled, [aria-disabled="true"] {
    background: var(--cpd-color-bg-action-primary-disabled) !important;
    color: var(--cpd-color-text-on-solid-primary) !important;
    cursor: not-allowed !important;
}

/* Cunningham bordered → Compound secondary */
.c__button--brand--bordered, .c__button--error--bordered {
    background: transparent !important;
    border: 1px solid var(--cpd-color-border-interactive-primary) !important;
    color: var(--cpd-color-text-primary) !important;
}

/* ================================================================
 * FORM/INPUT (Compound Form — specs exactes)
 * radius 8px, border gray-600, focus green + ring, height 36px+
 * ================================================================ */
input[type="text"], input[type="password"], input[type="email"],
input[type="number"], input[type="search"], input[type="url"],
input[type="tel"], input[type="date"], textarea, select {
    font-family: var(--cpd-font-family-sans) !important;
    font-size: 15px !important;
    color: var(--cpd-color-text-primary) !important;
    background: var(--cpd-color-bg-canvas-default) !important;
    border: 1px solid var(--cpd-color-border-interactive-primary) !important;
    border-radius: var(--cpd-radius-medium) !important;
    min-height: var(--cpd-space-9x);
    padding: 8px 12px;
    transition: border-color 0.1s, box-shadow 0.1s;
}

input:focus, textarea:focus, select:focus {
    outline: none !important;
    border-color: var(--cpd-color-text-action-accent) !important;
    box-shadow: 0 0 0 2px var(--cpd-color-bg-accent-subtle) !important;
}

input::placeholder, textarea::placeholder { color: var(--cpd-color-text-secondary) !important; }
label { font-weight: 500 !important; font-size: 13px !important; color: var(--cpd-color-text-primary); }

/* ================================================================
 * SEARCH (Compound Search — pilule 100% arrondie)
 * radius 9999px, height 36px, border gray-400, padding 6px 12px
 * ================================================================ */
input[type="search"],
.c__search-filter,
[class*="SearchBar"], [class*="search-bar"], [class*="searchBar"] {
    border-radius: var(--cpd-radius-pill-effect) !important;
    min-height: var(--cpd-space-9x);
    border: 1px solid var(--cpd-color-border-interactive-secondary) !important;
    padding: 6px 12px;
}

.c__search-filter input, .c__search-filter [class*="input"] {
    border-radius: var(--cpd-radius-pill-effect) !important;
    border: none !important;
    background: transparent !important;
    min-height: auto !important;
}

/* ================================================================
 * MENU/DROPDOWN (Compound FloatingMenu + MenuItem — specs exactes)
 * container : radius 12px, bg blanc, border 1px gray-400, SANS ombre
 * items : padding 8px 16px, min-width 200px, color gray-900, hover gray-300
 * ================================================================ */
.c__dropdown-menu,
[class*="dropdown-menu"],
[class*="popover-content"],
[class*="menu-content"],
[class*="Core_menu"]:not([class*="Backdrop"]) {
    border-radius: var(--cpd-space-3x) !important; /* 12px — spec Compound */
    background: var(--cpd-color-bg-canvas-default) !important;
    border: 1px solid var(--cpd-color-border-interactive-secondary) !important;
    box-shadow: none !important;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    gap: var(--cpd-space-1x);
    padding: var(--cpd-space-5x) var(--cpd-space-4x);
}

/* MenuItem : grid icon+label, padding 8px 16px, color gray-900 */
.c__dropdown-menu [role="menuitem"],
.c__dropdown-menu li,
[class*="menu--item"], [class*="menu__item"],
[class*="MenuItem"] {
    padding: var(--cpd-space-2x) var(--cpd-space-4x) !important;
    min-width: 200px;
    color: var(--cpd-color-text-secondary) !important;
    border-radius: var(--cpd-radius-small) !important;
    background: transparent !important;
    cursor: pointer;
}

.c__dropdown-menu [role="menuitem"]:hover,
[class*="menu--item"]:hover, [class*="menu__item"]:hover {
    background: var(--cpd-color-bg-subtle-primary) !important;
}

/* MenuSeparator */
.c__dropdown-menu hr,
[class*="separator"], [class*="Separator"], hr {
    border: none !important;
    border-top: 1px solid var(--cpd-color-separator-primary) !important;
    height: 1px;
    margin: var(--cpd-space-1x) 0;
}

/* ================================================================
 * SWITCH/TOGGLE (Compound Switch)
 * radius pill, bg blanc, border 1px gray-400, SANS ombre
 * ================================================================ */
[class*="switch"], [class*="toggle"], [class*="Switch"], [class*="Toggle"] {
    border-radius: var(--cpd-radius-pill-effect) !important;
    border: 1px solid var(--cpd-color-border-interactive-secondary) !important;
    background: var(--cpd-color-bg-canvas-default) !important;
    box-shadow: none !important;
}

input[type="checkbox"], input[type="radio"] {
    accent-color: var(--cpd-color-green-700) !important;
    width: 16px; height: 16px;
}

/* ================================================================
 * BADGE (Compound Badge)
 * padding-block 3px, radius pill
 * ================================================================ */
[class*="badge"], [class*="tag"], [class*="chip"], [class*="Badge"] {
    border-radius: var(--cpd-radius-pill-effect) !important;
    padding: 3px 10px !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    min-height: auto !important;
    box-shadow: none !important;
}

/* ================================================================
 * ALERT (Compound Alert)
 * ================================================================ */
[class*="alert"], [class*="Alert"] {
    border-radius: var(--cpd-radius-medium) !important;
    box-shadow: none !important;
}
[class*="alert-success"] { background: var(--cpd-color-green-300) !important; color: var(--cpd-color-green-900) !important; border: none !important; }
[class*="alert-error"], [class*="alert-danger"] { background: var(--cpd-color-red-300) !important; color: var(--cpd-color-red-900) !important; border: none !important; }

/* ================================================================
 * AVATAR (Compound Avatar — circulaire)
 * ================================================================ */
[class*="avatar"], [class*="Avatar"] {
    border-radius: 50% !important;
    box-shadow: none !important;
}

/* ================================================================
 * CARD/MODAL (Compound Dialog)
 * radius 8px, border 1px, SANS ombre
 * ================================================================ */
[class*="card"],
[class*="modal-content"],
[class*="dialog"]:not([class*="overlay"]),
[class*="sheet"] {
    border-radius: var(--cpd-radius-medium) !important;
    border: 1px solid var(--cpd-color-border-interactive-secondary);
    box-shadow: none !important;
    background: var(--cpd-color-bg-canvas-default);
}

/* ================================================================
 * NAV/SIDEBAR (pattern Element Web)
 * fond gray-300 (#f0f2f5), items hover gray-400, bordure droite
 * ================================================================ */
aside,
nav[class*="sidebar"],
[class*="Sidebar"]:not([class*="item"]):not([class*="content"]),
[class*="LeftMenu"]:not([class*="item"]):not([class*="text"]) {
    background: var(--cpd-color-bg-subtle-secondary) !important;
    border-right: 1px solid var(--cpd-color-border-interactive-secondary);
}

[class*="LeftMenu_boards"], [class*="LeftMenu_projects"] {
    background: transparent !important;
}

[class*="sidebar"] a, [class*="sidebar"] button,
[class*="LeftMenu"] button, [class*="nav-item"],
[class*="NavItem"], [class*="menu-item"] {
    border-radius: var(--cpd-radius-medium) !important;
    box-shadow: none !important;
}

[class*="sidebar"] a:hover, [class*="LeftMenu"] button:hover,
[class*="nav-item"]:hover {
    background: var(--cpd-color-bg-subtle-primary) !important;
}

/* Item actif UNIQUEMENT dans nav/tablist (pas les conteneurs actifs). */
nav a[class*="active"],
[role="tablist"] [aria-selected="true"],
[role="tab"][aria-selected="true"],
nav [aria-current="page"] {
    background: var(--cpd-color-bg-accent-subtle) !important;
    color: var(--cpd-color-text-action-accent) !important;
}

/* Nav tabs : underline pilule (Compound Nav) */
[role="tablist"] { border-bottom: 1px solid var(--cpd-color-gray-400); }
[role="tab"] { position: relative; padding: 16px 0; border: none; background: transparent; }
[role="tab"][aria-selected="true"]::after {
    content: ""; position: absolute; bottom: 0; left: 0; right: 0;
    height: 2px; border-radius: var(--cpd-radius-pill-effect) var(--cpd-radius-pill-effect) 0 0;
    background: var(--cpd-color-bg-action-primary-rest);
}

/* ================================================================
 * TABLES
 * ================================================================ */
th { font-weight: 500 !important; color: var(--cpd-color-text-secondary) !important; font-size: 13px !important; border-bottom: 1px solid var(--cpd-color-border-interactive-secondary); }
td { border-bottom: 1px solid var(--cpd-color-bg-subtle-primary); }

/* ================================================================
 * LIENS : vert Element
 * ================================================================ */
a:not([class*="btn"]):not([class*="button"]):not([class*="tile"]):not([class*="tab"]) {
    color: var(--cpd-color-text-action-accent);
    text-decoration: none;
}
a:not([class*="btn"]):hover { color: var(--cpd-color-bg-accent-hovered); }

/* ================================================================
 * TOOLTIP (Compound Tooltip : bg sombre, radius 4px, 11px)
 * ================================================================ */
[class*="tooltip"], [class*="Tooltip"] {
    background: var(--cpd-color-gray-1400) !important;
    color: #fff !important;
    border-radius: var(--cpd-radius-small) !important;
    padding: 6px 12px !important;
    font-size: 11px !important;
    font-weight: 500 !important;
    box-shadow: none !important;
}

/* ================================================================
 * PROGRESS (Compound Progress)
 * ================================================================ */
progress, [class*="progress"], [class*="Progress"] {
    border-radius: var(--cpd-radius-pill-effect) !important;
    accent-color: var(--cpd-color-green-700);
}

/* ================================================================
 * SCROLLBARS : fines, thumb pilule
 * ================================================================ */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background-color: var(--cpd-color-gray-500); border-radius: var(--cpd-radius-pill-effect); }

/* ================================================================
 * FOCUS VISIBLE : ring vert 2px
 * ================================================================ */
button:focus-visible, a:focus-visible,
input:focus-visible, select:focus-visible, textarea:focus-visible {
    outline: 2px solid var(--cpd-color-green-700) !important;
    outline-offset: 2px;
}

/* ================================================================
 * ZÉRO OMBRE — override global sur tous les composants
 * ================================================================ */
button, [class*="card"], [class*="menu"], [class*="dropdown"],
[class*="popover"], [class*="modal"]:not([class*="overlay"]),
[class*="tooltip"], [class*="panel"]:not([class*="header"]),
[class*="sheet"], .c__button, .c__dropdown-menu {
    box-shadow: none !important;
}

/* ================================================================
 * FIXES PAR APP (sélecteurs sûrs — buttons uniquement, pas conteneurs)
 * ================================================================ */

/* Messages : logo sans fond, boutons À propos/Paramètres sans ombre */
[class*="logo"], [class*="brand-logo"] { background: transparent !important; box-shadow: none !important; }
[class*="about"], [class*="settings"]:not([class*="content"]) { box-shadow: none !important; border-radius: var(--cpd-radius-medium) !important; }

/* Projects : cacher support/chapdocs/centre d'app */
[class*="support"], [class*="chapdocs"], [class*="help-center"],
[class*="HelpCenter"], [class*="app-center"],
a[href*="support"], a[href*="docs."] { display: none !important; }

/* Drive : contenu fond blanc, filtres non coupés */
[class*="explorer"] [class*="content"], [class*="my-files"] {
    background: var(--cpd-color-bg-canvas-default) !important;
}
[class*="filter"], [class*="Filter"], [class*="toolbar"] { overflow: visible !important; }

/* Drive : bouton upload/dossier VERT — UNIQUEMENT les <button> */
button[class*="upload"], button[class*="create-folder"],
button[class*="add-folder"], button[class*="new-folder"],
button[aria-label*="dossier"], button[class*="btn-add"] {
    background: var(--cpd-color-green-700) !important;
    color: #fff !important;
    border: none !important;
    border-radius: var(--cpd-radius-pill-effect) !important;
}

/* Overlay des modals Projects */
[class*="Core_menuBackdrop"] { background: rgba(0, 0, 0, 0.3) !important; }
