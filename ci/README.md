# ci/ — pipeline de distribution (phase 6)

- **Renovate** : bumps des pins du catalogue (`upstream_pin`, images) → une PR par
  brique, smoke tests obligatoires avant merge.
- **Gate licence** : scan des `LICENSE*` amont à chaque bump, diff contre
  docs/licences.md ; divergence = release bloquée (parade au risque « Element
  relicencie une version future »).
- **Smoke tests e2e** : par release, chaque brique démarre, répond à son healthcheck,
  authentifie via Keycloak.
- **SBOM** + régénération des `SOURCES.md` des déploiements actifs.
