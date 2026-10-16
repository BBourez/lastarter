# Modules LaStarter

## Modules disponibles

| Module | ID | Description | Backend | Portail |
|---|---|---|---|---|
| Transferts | `transfers` | Transfert de fichiers securise avec liens expires | Django | transfers.<domaine> |
| Projets | `projects` | Gestion de projets kanban collaboratif | Sails.js | projects.<domaine> |
| Discussions | `chat` | Messagerie chiffree E2E | Synapse (Matrix) | chat.<domaine> |
| Reunions | `meet` | Visioconference avec LiveKit | LiveKit SFU | meet.<domaine> |

## Activer / desactiver un module

```bash
# Activer un module
lastarter module enable transfers

# Desactiver un module (inaccessible pour tous)
lastarter module disable projects

# Lister les modules et leur etat
lastarter module list
```

## Ajouter un module au catalogue

1. Creer le backend (image Docker)
2. Creer le frontend dans `apps/<nom>/`
3. Ajouter le compose dans `deploy/docker/<nom>.yml`
4. Ajouter les routes dans la passerelle
5. Enregistrer le client OIDC dans le realm Keycloak

## Architecture d'un module

```
apps/<nom>/
├── package.json          # Dependances (@lastarter/ui, api, i18n, config)
├── vite.config.ts        # Build Vite avec alias vers packages/
├── index.html            # Point d'entree HTML
└── src/
    ├── main.tsx          # App principale avec Sidebar
    └── hooks/            # TanStack Query hooks (API)
```

Chaque module utilise :
- **@lastarter/ui** : composants (Sidebar, Button, Input, Modal...)
- **@lastarter/i18n** : traductions fr/en
- **@lastarter/api** : client HTTP + schemas Zod
- **@lastarter/config** : environnement + SSO Keycloak
