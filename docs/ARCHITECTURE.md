# Architecture LaStarter

## Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                        PASSERELLE (nginx/TLS)                    │
│   id.<domaine> → Keycloak    <app>.<domaine> → app frontend     │
└──────────────────────┬──────────────────────────────────────────┘
                       │
           ┌───────────┼───────────┬─────────────┐
           │           │           │             │
    ┌──────▼──┐ ┌─────▼────┐ ┌────▼─────┐ ┌────▼──────┐
    │ Keycloak │ │ Transfers │ │ Projects │ │  Portal   │
    │  (SSO)   │ │ frontend  │ │ frontend │ │ (static)  │
    └──────┬──┘ └─────┬────┘ └────┬─────┘ └───────────┘
           │           │           │
    ┌──────▼──┐ ┌─────▼────┐ ┌────▼─────┐
    │ kc_pg   │ │ Django   │ │ Sails.js │
    │ (PG 16) │ │ backend  │ │ backend  │
    └─────────┘ └─────┬────┘ └────┬─────┘
                      │           │
               ┌──────▼───────────▼──────┐
               │   Infrastructure         │
               │  PostgreSQL, Redis, S3   │
               └─────────────────────────┘
```

## Monorepo

```
lastarter/
├── packages/
│   ├── ui/         @lastarter/ui (design system Element/Compound)
│   ├── i18n/       @lastarter/i18n (multilingue fr/en)
│   ├── api/        @lastarter/api (client HTTP + schemas Zod)
│   └── config/     @lastarter/config (env + SSO Keycloak)
├── apps/
│   ├── portal/     Point d'entree (liste des modules)
│   ├── transfers/  Transfert de fichiers (frontend React)
│   └── projects/   Gestion de projets kanban (frontend React)
├── identity/       Keycloak (realm, theme login)
├── deploy/
│   ├── docker/     Docker Compose (core.yml, transfers.yml...)
│   └── kubernetes/ Helm charts
└── cli/            lastarter-cli (installateur Python)
```

## Packages

### @lastarter/ui (design system)

Base sur Compound (Element Web / Element Call).

**17 composants** : Button, Input, Badge, Avatar, Separator, Sidebar (double colonne), Modal (createPortal), Menu (FloatingMenu), Switch, Alert, Tabs, Toast (createPortal), Typography, Slot (asChild), ConfirmDialog (callable), Tooltip.

**5 hooks** : useToggle, useClickOutside, useMediaQuery, useDocumentTitle, useDebouncedValue.

**Store** : useAppStore (Zustand + persist) : user, theme, locale, modules, sidebar.

**Tokens** : `tokens.css` importe `@vector-im/compound-design-tokens` et definit les alias `--ls-*`.

### @lastarter/i18n (multilingue)

i18next + react-i18next. Locales fr/en partagees. Namespace commun (`common`, `sidebar`, `nav`, `auth`).

### @lastarter/api (contrat Zod)

Approche contrat-first (cf. Grafikart "Partager les types") :
- `schemas.ts` : schemas Zod qui generent les types TypeScript via `z.infer`
- `client.ts` : client HTTP base sur Ky avec interceptors auth
- `query-client.ts` : TanStack Query config

### @lastarter/config

Lecture environnement (Vite `import.meta.env` / Node `process.env`), config SSO Keycloak, redirections auth.

## Flux de donnees

```
┌──────────┐     TanStack Query      ┌──────────┐
│ React UI │ ────────────────────────► │ @lastarter/api │
│          │ ◄──────────────────────── │  (Ky + Zod)  │
└──────────┘    reponses validees      └──────┬───────┘
                                              │ fetch
                                       ┌──────▼───────┐
                                       │ Backend API  │
                                       │ Django/Sails │
                                       └──────────────┘
```

### Pattern DDD

Les schemas Zod dans `packages/api/src/schemas.ts` definissent les entites metier :
- `TransferSchema`, `ProjectSchema`, `CardSchema`, `CurrentUserSchema`
- Payloads : `CreateTransferPayloadSchema`, `CreateCardPayloadSchema`
- Types infères : `Transfer = z.infer<typeof TransferSchema>`

### Pattern TDD

Chaque composant a son fichier de test co-localise :
```
Button/
├── Button.tsx
├── Button.module.css
├── Button.test.tsx   ← tests co-localises
└── index.ts
```

## Securite

- **SSO Keycloak** : toutes les apps redirigent vers `id.<domaine>` si non connecte
- **Pas de page d'accueil** : URL racine = redirect auth ou app
- **TLS** : passerelle nginx sur port 8443 (CA locale en POC, certificats client en prod)
- **Secrets** : generes par le CLI, stockes dans `.env` (jamais committe)

## Build et deploiement

- **Dev** : `pnpm dev` (Vite dev server par app)
- **Build** : `pnpm build` (Vite build par app)
- **Docker** : `deploy/docker/*.yml` (compose par module)
- **K8s** : `deploy/kubernetes/` (Helm chart)

## CI/CD

GitHub Actions : lint (Biome) + test (Vitest) + typecheck (tsc strict). Tous bloquants.
