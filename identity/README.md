# identity/ — Keycloak as-code (phase 2)

Provisionnement automatique de l'identité d'un déploiement :

- `realm-lastarter.json` — realm gabarit (clients OIDC par brique, rôles, branding de
  la page de login). Inspiré du realm de dev amont de drive (`docker/auth/realm.json`),
  adapté : un seul realm `lastarter`, un client OIDC par brique.
- Provisionnement au déploiement : import au premier démarrage (`--import-realm`),
  puis pilotage par l'API admin (jamais de ré-import écrasant).

Chaque brique déclare son client dans son manifeste catalogue (`[oidc]`) :
`lastarter deploy` (phase 2) lit ces déclarations et crée/met à jour les clients.
