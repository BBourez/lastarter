# @lastarter/ui

Librairie de composants React pour LaStarter — **copie conforme d'Element Web (Compound)**, entièrement customisabile via tokens CSS.

## Installation

```bash
pnpm add @lastarter/ui
```

## Usage

```tsx
import { Sidebar, Button } from "@lastarter/ui";
import "@lastarter/ui/src/tokens.css";
import "@lastarter/ui/src/fonts.css";

function App() {
    return (
        <div style={{ display: "flex" }}>
            <Sidebar
                searchPlaceholder="Rechercher…"
                onSearchClick={() => console.log("search")}
                sections={[
                    {
                        title: "Fichiers",
                        items: [
                            { icon: "📁", label: "Mes fichiers", href: "/my-files", active: true },
                            { icon: "⭐", label: "Favoris", href: "/favorites" },
                            { icon: "🗑", label: "Corbeille", href: "/trash" },
                        ],
                    },
                ]}
                user={{ displayName: "Jean Dupont", email: "jean@acme.com" }}
                onSettingsClick={() => console.log("settings")}
                onUserClick={() => console.log("profile")}
            />
            <main style={{ flex: 1 }}>
                <Button kind="accent">Nouveau dossier</Button>
                <Button kind="secondary">Annuler</Button>
            </main>
        </div>
    );
}
```

## Customisation (comme shadcn/ui)

Tous les tokens sont surchargeables via CSS :

```css
:root {
    /* Changer la couleur primaire (ex: orange pour ACME) */
    --ls-color-primary: #ff6b35;
    --ls-color-primary-hover: #e55a2b;

    /* Changer la largeur de la sidebar */
    --ls-sidebar-width: 300px;

    /* Changer la police */
    --ls-font-family: 'MaPolice', sans-serif;
}
```

## Composants

| Composant | Description | Source |
|---|---|---|
| `Sidebar` | Sidebar Element Web : fond blanc, 260px, user menu en bas | `_LeftPanel.pcss` |
| `Button` | Pilule 9999px, primary/secondary/tertiary/accent/destructive | `compound-web/Button` |
| `Input` | Radius 8px, focus ring vert | `compound-web/Form` |
| `Menu` | Dropdown 12px, sans ombre | `compound-web/Menu` |

## Structure (comme shadcn — le code vit dans votre repo)

```
packages/ui/src/
├── tokens.css              ← Design tokens (customisables)
├── fonts.css               ← Inter 400/500/600
├── components/
│   ├── Sidebar/            ← Sidebar + UserMenu + Search
│   ├── Button/             ← Button (5 variantes)
│   ├── Input/              ← Input/Textarea
│   ├── Menu/               ← Dropdown/FloatingMenu
│   └── Modal/              ← Dialog
└── index.ts                ← Exports publics
```
