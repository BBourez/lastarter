# Schéma des manifestes de briques

Chaque brique du catalogue est un fichier `<nom>.toml`. Format consommé par
`lastarter-cli` (stdlib `tomllib`) — voir `cli/lastarter_cli/catalogue.py` pour la
définition canonique (dataclass `Brick`).

```toml
[brick]
name = "drive"                        # identifiant unique (slug)
title = "Drive — fichiers collaboratifs"
category = "collaboration"            # collaboration | communication | fondation
description = "…"
license = "MIT"                       # licence amont (clé du registre docs/licences.md)
upstream_repo = "https://github.com/suitenumerique/drive"
upstream_pin = "…"                    # version / ref épinglée (bump via Renovate)
core = false                          # true = toujours installée (fondation, ex. keycloak)
requires = ["keycloak"]               # dépendances vers d'autres BRIQUES (pas services internes)
maturity = "stable"                   # stable | planned — "planned" = à venir (phase future),
                                      # caché de la sélection CLI par défaut (--all pour voir)

[oidc]                                # provisionnement du client Keycloak (phase 2)
client_id = "drive"
scopes = "openid email"

[branding.env]                        # variables de marque blanche (surchargeables
BRAND_NAME = "…"                      # par branding/<client>.toml)

[env]                                 # variables d'environnement principales (brouillon
KEY = "valeur | {domain} | {secret}"  # .env généré à l'init ; {domain} substitué)

[compose]                             # orchestration + informationnel
profile = "drive"                     # profil docker-compose de la brique
infra_services = ["postgresql", …]    # services à démarrer AVANT la migration
migrate_service = "app"               # service exécutant la migration (optionnel)
migrate_command = "python manage.py…" # commande de migration (optionnel)
services = ["app", "frontend", "…"]   # services internes (postgres, redis… inclus)
extras = ["collabora", "onlyoffice"]  # services optionnels activables

# Jetons disponibles dans [env] / [branding.env] :
#   {domain}     — domaine client (sans schéma)
#   {origin}     — schéma + domaine (http en local, https sinon)
#   {domain_s3}  — domaine où le S3 média est exposé (POC : host:port rustfs)
#   {brand_name} — marque affichée
#   {secret:KEY} — secret du coffre (jeton conservé dans les drafts committables,
#                  substitué uniquement dans .runtime/ au déploiement)

[notes]
warnings = "…"                        # points d'attention pour l'installateur
```

Règles :

- `requires` ne référence que des briques du catalogue ; les dépendances *internes*
  (bases de données, cache, stockage S3…) restent dans le profil compose de la brique.
- `{domain}` dans `[env]` est substitué par le domaine client à l'`init` ;
  `{secret:<nom>}` déclenche la génération d'un secret fort (jamais re-généré ensuite).
- Toute entrée doit exister dans `docs/licences.md` (gate licence).
