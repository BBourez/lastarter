# Schéma des manifestes de briques

Chaque brique du catalogue est un fichier `<nom>.toml`. Format consommé par
`lastarter-cli` (stdlib `tomllib`) — voir `cli/lastarter_cli/catalogue.py` pour la
définition canonique (dataclass `Brick`).

```toml
[brick]
name = "drive"                        # identifiant unique (slug)
title = "Drive — fichiers collaboratifs"
category = "collaboration"            # collaboration | communication | storage | fondation
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

[branding.custom_theme]               # palette / personnalisation (optionnel) :
colors = { primary = "#0bc491" }      # consommé par le CLI pour générer, depuis la
logo = "branding/logo.svg"            # même source, le JSON de thème NATIF des apps
                                      # (drive THEME_CUSTOMIZATION_FILE_PATH, element-web
                                      # custom_themes) et le dossier branding servi par
                                      # la passerelle sur /__lastarter/

[env]                                 # variables d'environnement principales (brouillon
KEY = "valeur | {domain} | {secret}"  # .env généré à l'init ; {domain} substitué)

[compose]                             # orchestration + exposition passerelle
profile = "drive"                     # profil logique de la brique
infra_services = ["drive_postgresql", …]   # services (préfixés <brique>_) AVANT migration
migrate_service = "drive_app"         # service exécutant la migration (optionnel)
migrate_command = "python manage.py…" # commande de migration (optionnel)
route_label = "drive"                 # sous-domaine : <label>.<domaine>
frontend_target = "drive_frontend:3000"  # cible de la passerelle pour /
api_target = "drive_app:8000"            # cible de la passerelle pour /api/
access = "public"                     # public (défaut) | vpn (LAN + WireGuard/CGNAT
                                      # + loopback uniquement — derrière un VPN)
extra_servers = [                     # serveurs additionnels (ex. SFU websocket)
  { label = "livekit", target = "meet_livekit:7880" }
]
services = ["drive_app", "drive_frontend", "…"]  # inventaire (informationnel)
extras = ["collabora", "onlyoffice"]  # services optionnels activables

# RÈGLE ANTI-COLLISION : tous les services compose sont préfixés (<brique>_)
# et chaque conteneur d'infra lit son env_file de brique (POSTGRES_*, RUSTFS_*,
# GARAGE_* déclarés dans [env]) — JAMAIS de ${} partagé entre briques (l'union
# compose.env écraserait DB_NAME/AWS_S3_* d'une autre brique).

# Jetons disponibles dans [env] / [branding.env] :
#   {domain}     — domaine apex client (SSO), sans schéma
#   {sso_origin} — schéma + apex (ex. https://acme.example.com)
#   {origin}     — schéma + <label>.<domaine> (origine de CETTE app)
#   {app_host}   — <label>.<domaine> (sans schéma, pour ALLOWED_HOSTS)
#   {ws}         — "ws" en local, "wss" en production
#   {django_configuration} — "Development" en local (http), "Feature" en prod
#                  (les classes Production/Feature forcent SECURE_SSL_REDIRECT)
#   {domain_s3}  — host:port du S3 média public (POC)
#   {brand_name} — marque affichée
#   {secret:KEY} — secret du coffre (jeton conservé dans les drafts committables,
#                  substitué uniquement dans .runtime/ au déploiement)

[notes]
warnings = "…"                        # points d'attention pour l'installateur
```

Exemple — brique meet (visio, images amont suitenumerique/meet) :

```toml
[brick]
name = "meet"
title = "Meet — visioconférence"
category = "communication"
license = "MIT"
upstream_repo = "https://github.com/suitenumerique/meet"
upstream_pin = "v1.36.2"
requires = ["keycloak"]
extra_secrets = ["meet_oidc_secret", "meet_django_secret_key", "meet_livekit_secret",
                 "meet_s3_secret", "meet_db_password"]

[oidc]
client_id = "meet"

[env]
MEET_BACKEND_IMAGE = "lasuite/meet-backend:v1.36.2"   # pinné — JAMAIS latest
FRONTEND_CUSTOM_CSS_URL = "https://{domain}/__lastarter/theme.css"
LIVEKIT_API_SECRET = "{secret:meet_livekit_secret}"

[compose]
route_label = "meet"
frontend_target = "meet_frontend:8080"
api_target = "meet_backend:8000"
extra_servers = [{ label = "livekit", target = "meet_livekit:7880" }]
services = ["meet_postgresql", "meet_redis", "meet_rustfs", "meet_createbuckets",
            "meet_livekit", "meet_backend", "meet_frontend"]
```

Règles :

- `requires` ne référence que des briques du catalogue ; les dépendances *internes*
  (bases de données, cache, stockage S3…) restent dans le profil compose de la brique.
- `{domain}` dans `[env]` est substitué par le domaine client à l'`init` ;
  `{secret:<nom>}` déclenche la génération d'un secret fort (jamais re-généré ensuite).
- Toute entrée doit exister dans `docs/licences.md` (gate licence).
- Toujours PINNER les images à une version exacte — jamais `latest` (les tags
  `latest` des images lasuite suivent `main` = preprod). Un bump de pin est une
  décision de roadmap : la commande `check-updates` liste les écarts amont.
