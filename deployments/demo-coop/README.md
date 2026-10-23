# Déploiement « Demo Coop »

- Domaine : localhost:8443
- Marque : LaStarter
- Briques : keycloak, discussions, drive, meet

## Contenu

- `lastarter.toml` — manifeste du déploiement (versions épinglées).
- `answers.json` — réponses du questionnaire (rejeu `lastarter init`).
- `branding/` — logo du client (servi par la passerelle sur `/__lastarter/branding/`).
- `env/<brique>.env` — brouillons d'environnement committables (jetons `{secret:…}` substitués au déploiement depuis `secrets.env`).
- `secrets.env` — secrets réels : **ne jamais commiter** (chiffrer : SOPS/ansible-vault, phase 3).
- `SOURCES.md` — mentions licences (obligation copyleft).

## Étapes suivantes

1. Ajuster `env/*.env` si besoin (valeurs par défaut issues du catalogue).
2. `lastarter deploy --client <slug> --pull` : gates → rendu `.runtime/` (secrets, realm Keycloak, thème, branding) → infra → migrations → `up -d --wait`.
3. `lastarter smoke --client <slug>` : surfaces HTTP (portail, SSO, apps).
