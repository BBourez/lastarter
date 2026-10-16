# Design System LaStarter

Base sur Compound (Element Web / Element Call). Tous les composants utilisent les memes tokens CSS surchargeables.

## Tokens

Definis dans `packages/ui/src/tokens.css`, bases sur `@vector-im/compound-design-tokens` (npm officiel Element).

### Couleurs

| Token | Valeur par defaut | Usage |
|---|---|---|
| `--ls-color-primary` | #0bc491 (vert Element) | Accents, liens, boutons accent |
| `--ls-color-bg` | #ffffff | Fond des pages et sidebars |
| `--ls-color-bg-subtle` | #f0f2f5 | Hover, fonds secondaires |
| `--ls-color-bg-inverted` | #1b1d22 | Boutons primary (gris fonce) |
| `--ls-color-text` | #1b1d22 | Texte principal |
| `--ls-color-text-secondary` | #656d77 | Texte secondaire |
| `--ls-color-border` | #e1e6ec | Bordures |

### Geometrie

| Token | Valeur | Usage |
|---|---|---|
| `--ls-radius-pill` | 9999px | Boutons (pilule) |
| `--ls-radius-md` | 8px | Inputs, cartes, items sidebar |
| `--ls-radius-menu` | 12px | Menus, dropdowns |

### Typographie

| Token | Valeur | Usage |
|---|---|---|
| `--ls-font-family` | Inter | Police principale |
| `--ls-font-size-md` | 15px | Corps de texte |
| `--ls-font-size-h2` | 24px | Titres de page |

## Composants

| Composant | Description | Spec Compound |
|---|---|---|
| Button | Pilule, 5 variantes, 3 tailles | data-kind, data-size |
| Input | Radius 8px, focus ring vert | Form/TextInput |
| Sidebar | Double colonne : SpacePanel 68px + LeftPanel 260px | LeftPanel + SpacePanel |
| Modal | Overlay + dialog radius 8px | Dialog |
| Menu | FloatingMenu radius 12px, sans ombre | Menu/FloatingMenu |
| Badge | Pilule, 6 couleurs | Badge |
| Avatar | Circulaire avec initiales | Avatar |
| Switch | Toggle pilule | Switch |
| Alert | Success/Error/Warning/Info | Alert |
| Separator | 1px horizontal/vertical | Separator |

## Surcharge (marque blanche)

```css
:root {
    /* Changer la couleur primaire (ex: orange pour ACME) */
    --ls-color-primary: #ff6b35;
    --ls-color-primary-hover: #e55a2b;
    --ls-color-primary-subtle: #fff3ed;

    /* Changer la police */
    --ls-font-family: 'MaPolice', system-ui, sans-serif;

    /* Ajuster la largeur de la sidebar */
    --ls-sidebar-width: 300px;
}
```

## Schemas Zod (contrats API)

Les types sont definis dans `packages/api/src/schemas.ts` avec des schemas Zod qui servent a la fois :
- De types TypeScript statiques (z.infer)
- De validation runtime des reponses API
- De documentation vivante du contrat front/backend
