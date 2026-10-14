# ci/ — pipeline de distribution (phase 6)

## En place

- **Renovate** : [`../renovate.json5`](../renovate.json5) — bumps des pins du
  catalogue (`upstream_image` + `upstream_pin`, manager regex docker) et des
  images des fichiers compose. Chaque PR de bump passe la CI puis un smoke
  `deploy` + `smoke` en recette.
- **CI GitHub Actions** : [`../.github/workflows/ci.yml`](../.github/workflows/ci.yml)
  — tests unitaires (offline) + gate licence + cohérence catalogue à chaque push.
- **Gate licence** (CLI) : `python -m lastarter_cli licenses` — liste blanche
  SPDX (`cli/lastarter_cli/cmd/licenses.py`) + croisement avec le registre
  `docs/licences.md`. Toute licence inconnue ou brique absente du registre
  bloque la release.
- **Smoke tests** (CLI) : `python -m lastarter_cli smoke --client <slug>` —
  vérifie chaque surface exposée en HTTPS **strict** (CA du déploiement, SANs
  explicites, hostname matching) : portail, découverte SSO, frontends, APIs.
  Exit non nul = release bloquée. Résolution `*.localhost` locale incluse
  (comportement navigateur).
- **SBOM** (CLI) : `python -m lastarter_cli sbom --client <slug>` — inventaire
  CycloneDX 1.5 des briques épinglées (version, licence, source amont) écrit
  dans `deployments/<slug>/sbom.json`.

## À venir (suite phase 6)

- Runner self-hosted Docker pour `deploy + smoke` automatiques en recette à
  chaque bump mergé.
- Durcissement prod : HSTS long, CSP stricte, en-têtes sécurité passerelle.
- Diff automatique `docs/licences.md` ↔ fichiers LICENSE amont à chaque bump.
