# Déploiement « Demo Coop »

- Domaine : localhost:8443
- Marque : LaStarter
- Briques : keycloak, discussions, drive, element-call

## Contenu

- `lastarter.toml` — manifeste du déploiement (versions épinglées).
- `answers.json` — réponses du questionnaire (rejeu `lastarter init`).
- `env/<brique>.env` — brouillons d'environnement committables (jetons `{secret:…}` substitués au déploiement depuis `secrets.env`).
- `secrets.env` — secrets réels : **ne jamais commiter** (chiffrer : SOPS/ansible-vault, phase 3).
- `SOURCES.md` — mentions licences (obligation copyleft).

## Étapes suivantes (phase 2)

1. Ajuster `env/*.env` si besoin (valeurs par défaut issues du catalogue).
2. `lastarter deploy` (à venir) : compose + realm Keycloak provisionné.
