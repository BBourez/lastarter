# LaStarter

Suite collaborative souveraine B2B avec design system Element (Compound).

## Architecture

```
lastarter/
├── packages/           Librairies partagees
│   ├── ui/             Design system (11+ composants Element Web)
│   ├── i18n/           Multilingue (fr/en)
│   ├── api/            Client HTTP (Ky) + TanStack Query + types metier
│   └── config/         Environnement + SSO Keycloak
├── apps/               Applications frontend
│   ├── portal/         Point d'entree (liste des modules)
│   ├── transfers/      Transfert de fichiers (backend Django)
│   └── projects/       Gestion de projets kanban (backend Sails.js)
├── identity/           Keycloak (SSO, realm, theme login)
├── deploy/             Docker Compose + Kubernetes
└── cli/                Installateur (lastarter-cli)
```

## Quick start

```bash
# Installer les dependances
pnpm install

# Developper (toutes les apps en parallele)
pnpm dev

# Build
pnpm build

# Tests
pnpm test

# Lint
pnpm lint
```

## Design system

Base sur Compound (Element Web / Element Call) :
- Tokens : `packages/ui/src/tokens.css` (importe `@vector-im/compound-design-tokens`)
- Composants : `packages/ui/src/components/` (Button, Input, Sidebar, Modal, Menu, etc.)
- Police : Inter (400/500/600)

Tous les tokens sont surchargeables :
```css
:root {
    --ls-color-primary: #ff6b35;
}
```

## Modules

| Module | Description | Backend |
|---|---|---|
| transfers | Transfert de fichiers securise | Django |
| projects | Gestion de projets kanban | Sails.js |
| chat | Messagerie chiffree | Synapse (Matrix) |
| meet | Reunions video | LiveKit |

Chaque module peut etre active/desactive via le CLI.

## Licence

Proprietaire. Voir LICENSE.
   amont (correctifs de sécurité inclus) continuent d'affluer gratuitement.
2. **L'intégration vit dans la couche orchestration** : identité unique (Keycloak/OIDC),
   portail SSO, branding par variables d'environnement, déploiement modulaire.
   Jamais dans le code des applications.
3. **Installateur à la carte.** `lastarter-cli` pose un questionnaire (quelles briques
   pour ce client ? quel domaine ? quel thème ?) et génère un arbre de configuration
   versionné Git, prêt à déployer en docker-compose (mono-VM) ou Kubernetes.
4. **Conformité licences outillée.** Chaque déploiement embarque une page de mentions
   sources (`SOURCES.md`) ; la CI contrôle les licences à chaque bump de version.

## Structure du dépôt

```
lastarter/
├── catalogue/     Briques épinglées (manifestes TOML : version, deps, branding, env)
├── cli/           lastarter-cli (Python 3.12+, zéro dépendance) — init / deploy / …
├── deploy/        compose/ (profils docker-compose mono-VM) et k8s/ (Helm umbrella)
├── identity/      Realm Keycloak as-code : clients OIDC de chaque brique
├── branding/      Thèmes clients (logos, couleurs) injectés par variables d'env
├── portal/        Portail SSO d'entrée unique (launchpad + annuaire des briques)
├── ci/            Renovate (pins), smoke tests, SBOM, gate licence, releases
├── docs/          Architecture, registre des licences
└── deployments/   Arbres de configuration générés par le CLI (un dossier par client)
```

## Démarrage rapide (maquette phase 1)

```bash
cd cli
python -m lastarter_cli list                 # lister les briques du catalogue
python -m lastarter_cli init                 # questionnaire interactif
# variante scriptable :
python -m lastarter_cli init --client "ACME" --domain acme.example.com \
    --bricks keycloak,drive --non-interactive --output ../deployments
# POC local (domaine localhost:8083) :
python -m lastarter_cli deploy --client demo-coop --pull
python -m lastarter_cli ps --client demo-coop
```

Le résultat est un dossier `deployments/acme/` contenant le manifeste client, les
brouillons d'environnement, les secrets générés (à chiffrer) et les mentions sources.
`deploy` orchestre docker-compose : infra (healthchecks) → migrations → pile complète.

## Feuille de route

| Phase | Contenu | Statut |
|---|---|---|
| 1 | Fondations : scaffold, catalogue (keycloak, drive), maquette CLI `init` | ✅ |
| 2 | POC vertical : compose keycloak+drive, realm as-code, branding, `deploy` | ✅ validé E2E |
| 3 | Multi-apps : passerelle sous-domaines, **meet** (livekit/garage), clients OIDC via API admin | ✅ + **transfers** (edge Caddy, digest GHCR) validé E2E — messages restant |
| 4 | Chat : **synapse** (homeserver as-code) + **element-web** (recoloré par config), SSO complet | ✅ validé E2E |
| 5a | **Portail** : launchpad statique sur l'apex, tuiles générées par brique | ✅ validé E2E |
| 5b | Helm umbrella (k8s) | ⏳ |
| 6 | Industrialisation : Renovate, smoke tests, SBOM, gate licence | |

## Origine des briques et licences

LaStarter assemble des logiciels libres, principalement l'écosystème
**La Suite numérique** (DINUM/ANCT, licence MIT) et la stack **Matrix** (Synapse AGPL-3.0,
Tchap AGPL-3.0/GPL-3.0 au choix, LiveKit Apache-2.0). Voir
[docs/licences.md](docs/licences.md) — le registre complet et les obligations associées.

LaStarter n'est ni affilié ni endorsement par ces éditeurs ; les marques « La Suite »,
« Element », etc. appartiennent à leurs titulaires respectifs et ne sont pas utilisées
dans l'interface livrée aux clients (branding LaStarter ou du client final).
