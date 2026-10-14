# deployments/ — arbres de configuration clients

Un dossier par client, généré par `lastarter init` (voir cli/README.md).

- Committable : `lastarter.toml` (manifeste), `answers.json` (rejeu), `env/*.env`
  (jetons `{secret:…}`), `SOURCES.md` (mentions licences).
- **Jamais committable** : `secrets.env` (gitignoré) — à chiffrer (SOPS /
  ansible-vault) hors repo, phase 3.
